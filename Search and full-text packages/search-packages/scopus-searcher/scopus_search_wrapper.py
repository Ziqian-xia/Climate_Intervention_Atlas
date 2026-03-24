#!/usr/bin/env python3
"""
Scopus search wrapper via Elsevier Search API.

Purpose:
- Input Scopus query strings
- Retrieve Scopus search metadata in batches
- Export summary CSV + full JSONL for workflow use
"""

import argparse
import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Iterable

import requests
from tqdm import tqdm


API_BASE_URL = "https://api.elsevier.com/content/search/scopus"
DEFAULT_TIMEOUT = 45
DEFAULT_MAX_RETRIES = 4
DEFAULT_BACKOFF_SECONDS = 1.0


def slugify(s: str) -> str:
    out = re.sub(r"[^\w\-]+", "_", (s or "").strip())
    out = out.strip("_")
    return out[:80] or "query"


def unique_keep_order(items: Iterable[str]) -> list[str]:
    out = []
    seen = set()
    for item in items:
        x = (item or "").strip()
        if not x or x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def load_queries_from_file(path: Path, query_column: str) -> list[str]:
    ext = path.suffix.lower()
    if ext == ".txt":
        lines = []
        for line in path.read_text(encoding="utf-8").splitlines():
            x = line.strip()
            if not x or x.startswith("#"):
                continue
            lines.append(x)
        return unique_keep_order(lines)
    if ext == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return []
            if query_column not in reader.fieldnames:
                raise ValueError(
                    f"CSV column '{query_column}' not found. Available columns: {reader.fieldnames}"
                )
            return unique_keep_order([(row.get(query_column) or "").strip() for row in reader])
    if ext == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                return unique_keep_order([str(x.get(query_column, "")).strip() for x in data])
            return unique_keep_order([str(x).strip() for x in data])
        if isinstance(data, dict):
            if "queries" in data and isinstance(data["queries"], list):
                return unique_keep_order([str(x).strip() for x in data["queries"]])
            if "data" in data and isinstance(data["data"], list):
                return unique_keep_order(
                    [str(x.get(query_column, "")).strip() for x in data["data"] if isinstance(x, dict)]
                )
        return []
    if ext == ".jsonl":
        out = []
        for line in path.read_text(encoding="utf-8").splitlines():
            x = line.strip()
            if not x:
                continue
            obj = json.loads(x)
            if isinstance(obj, dict):
                out.append(str(obj.get(query_column, "")).strip())
            else:
                out.append(str(obj).strip())
        return unique_keep_order(out)
    raise ValueError(f"Unsupported query file type: {ext}. Use txt/csv/json/jsonl.")


class ScopusSearchWrapper:
    def __init__(
        self,
        api_key: str,
        inst_token: str = "",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        requests_per_second: float = 0.0,
    ):
        self.api_key = (api_key or "").strip()
        self.inst_token = (inst_token or "").strip()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = requests.Session()

        self.rps = requests_per_second if requests_per_second > 0 else 5.0
        self.min_interval = 1.0 / self.rps
        self._last_request_ts = 0.0

    def _headers(self) -> dict:
        h = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json",
        }
        if self.inst_token:
            h["X-ELS-Insttoken"] = self.inst_token
        return h

    def _throttle(self):
        now = time.time()
        wait = self.min_interval - (now - self._last_request_ts)
        if wait > 0:
            time.sleep(wait)

    def _request_with_retry(self, params: dict) -> requests.Response:
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                self._throttle()
                resp = self.session.get(
                    API_BASE_URL,
                    params=params,
                    headers=self._headers(),
                    timeout=self.timeout,
                )
                self._last_request_ts = time.time()
                if resp.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries:
                        retry_after = resp.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            sleep_s = max(float(retry_after), self.backoff_seconds)
                        else:
                            sleep_s = self.backoff_seconds * (2 ** attempt)
                        time.sleep(sleep_s)
                        continue
                return resp
            except requests.RequestException as e:
                last_exc = e
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * (2 ** attempt))
                    continue
                raise
        if last_exc:
            raise last_exc
        raise RuntimeError("Unexpected retry state")

    def search_query(
        self,
        query: str,
        count_per_page: int = 25,
        max_results: int = 1000,
        view: str = "",
    ) -> dict:
        page_size = max(1, min(200, count_per_page))
        params = {"query": query, "start": 0, "count": page_size}
        if view:
            params["view"] = view

        results = []
        calls = 0
        total_count = None
        last_status = ""

        while len(results) < max_results:
            try:
                resp = self._request_with_retry(params=params)
            except Exception as e:
                return {
                    "success": False,
                    "status": f"error:{str(e)[:120]}",
                    "query": query,
                    "calls": calls,
                    "results": results,
                    "meta_count": total_count,
                }
            calls += 1
            last_status = resp.headers.get("X-ELS-Status", "")

            if resp.status_code >= 400:
                return {
                    "success": False,
                    "status": f"http_{resp.status_code}",
                    "error": (resp.text or "").strip().replace("\n", " ")[:240],
                    "query": query,
                    "calls": calls,
                    "results": results,
                    "meta_count": total_count,
                    "x_els_status": last_status,
                }

            try:
                payload = resp.json()
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "status": "invalid_json",
                    "query": query,
                    "calls": calls,
                    "results": results,
                    "meta_count": total_count,
                    "x_els_status": last_status,
                }

            sr = payload.get("search-results", {}) or {}
            if total_count is None:
                try:
                    total_count = int(sr.get("opensearch:totalResults", "0") or 0)
                except Exception:
                    total_count = 0

            batch = sr.get("entry", []) or []
            if isinstance(batch, dict):
                batch = [batch]

            if not batch:
                break

            for e in batch:
                results.append(e)
                if len(results) >= max_results:
                    break

            params["start"] = int(params.get("start", 0)) + len(batch)
            if total_count is not None and params["start"] >= total_count:
                break

        return {
            "success": True,
            "status": "success",
            "query": query,
            "calls": calls,
            "results": results,
            "meta_count": total_count,
            "x_els_status": last_status,
        }


def main():
    parser = argparse.ArgumentParser(description="Scopus query wrapper via Elsevier Search API")
    parser.add_argument("--api-key", default=os.getenv("ELSEVIER_API_KEY", ""), help="Elsevier API key with Scopus access")
    parser.add_argument("--inst-token", default=os.getenv("ELSEVIER_INST_TOKEN", ""), help="Elsevier institution token (optional)")
    parser.add_argument("--query", action="append", default=[], help="Scopus query string, e.g. TITLE-ABS-KEY(heat AND mortality)")
    parser.add_argument("--query-file", default="", help="Query file: txt/csv/json/jsonl")
    parser.add_argument("--query-column", default="query", help="Query column in csv/json object inputs")
    parser.add_argument("--count-per-page", type=int, default=25, help="Page size (1-200)")
    parser.add_argument("--max-results-per-query", type=int, default=1000)
    parser.add_argument("--view", default="", help="Optional Scopus API view, e.g. STANDARD, COMPLETE")
    parser.add_argument("--keep-duplicates", action="store_true", help="Keep duplicate EIDs across queries")
    parser.add_argument("--requests-per-second", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--backoff-seconds", type=float, default=DEFAULT_BACKOFF_SECONDS)
    parser.add_argument("--out-dir", default="scopus_search_outputs")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing API key. Use --api-key or ELSEVIER_API_KEY.")

    file_queries = []
    if args.query_file:
        p = Path(args.query_file).resolve()
        if not p.exists():
            raise SystemExit(f"Query file not found: {p}")
        file_queries = load_queries_from_file(p, args.query_column)

    queries = unique_keep_order([*args.query, *file_queries])
    if not queries:
        raise SystemExit("No query provided. Use --query and/or --query-file.")

    out_dir = Path(args.out_dir).resolve()
    query_runs_dir = out_dir / "query_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    query_runs_dir.mkdir(parents=True, exist_ok=True)

    client = ScopusSearchWrapper(
        api_key=args.api_key,
        inst_token=args.inst_token,
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
        requests_per_second=args.requests_per_second,
    )

    run_summary = []
    summary_rows = []
    seen_eids = set()
    total_stored = 0

    full_jsonl = out_dir / "works_full.jsonl"
    summary_csv = out_dir / "works_summary.csv"
    summary_json = out_dir / "run_summary.json"

    with full_jsonl.open("w", encoding="utf-8") as jf:
        for idx, query in enumerate(tqdm(queries, desc="Scopus queries"), start=1):
            res = client.search_query(
                query=query,
                count_per_page=args.count_per_page,
                max_results=args.max_results_per_query,
                view=args.view,
            )

            row = {
                "query_index": idx,
                "query": query,
                "status": res.get("status"),
                "success": bool(res.get("success")),
                "calls": res.get("calls", 0),
                "meta_count": res.get("meta_count"),
                "returned_results": len(res.get("results", [])),
                "stored_results": 0,
                "x_els_status": res.get("x_els_status", ""),
                "raw_query_path": "",
                "error": res.get("error", ""),
            }

            raw_path = query_runs_dir / f"{idx:03d}_{slugify(query)}.json"
            raw_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
            row["raw_query_path"] = str(raw_path)

            if res.get("success"):
                for e in res.get("results", []):
                    eid = (e.get("eid") or "").strip()
                    if not args.keep_duplicates and eid and eid in seen_eids:
                        continue
                    if eid:
                        seen_eids.add(eid)

                    rec = {
                        "query_index": idx,
                        "query": query,
                        "eid": eid,
                        "doi": (e.get("prism:doi") or "").strip().lower(),
                        "title": (e.get("dc:title") or "").strip(),
                        "description": (e.get("dc:description") or "").strip(),
                        "creator": (e.get("dc:creator") or "").strip(),
                        "publication_name": (e.get("prism:publicationName") or "").strip(),
                        "cover_date": (e.get("prism:coverDate") or "").strip(),
                        "aggregation_type": (e.get("prism:aggregationType") or "").strip(),
                        "subtype": (e.get("subtypeDescription") or "").strip(),
                        "citedby_count": e.get("citedby-count", ""),
                    }
                    summary_rows.append(rec)
                    jf.write(json.dumps({"query_index": idx, "query": query, "entry": e}, ensure_ascii=False) + "\n")
                    row["stored_results"] += 1
                    total_stored += 1

            run_summary.append(row)

    cols = [
        "query_index",
        "query",
        "eid",
        "doi",
        "title",
        "description",
        "creator",
        "publication_name",
        "cover_date",
        "aggregation_type",
        "subtype",
        "citedby_count",
    ]
    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in summary_rows:
            w.writerow({c: r.get(c, "") for c in cols})

    summary_json.write_text(json.dumps(run_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    ok_queries = sum(1 for x in run_summary if x.get("success"))
    print(f"Done. queries={len(queries)}, success_queries={ok_queries}, failed_queries={len(queries)-ok_queries}")
    print(f"Stored records: {total_stored}")
    print(f"Run summary: {summary_json}")
    print(f"Works summary CSV: {summary_csv}")
    print(f"Full metadata JSONL: {full_jsonl}")
    print(f"Per-query logs: {query_runs_dir}")


if __name__ == "__main__":
    main()
