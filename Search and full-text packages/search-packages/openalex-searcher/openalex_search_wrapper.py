#!/usr/bin/env python3
"""
OpenAlex search wrapper for workflow step-2:
- Input OpenAlex search query strings
- Retrieve many works with metadata
- Export full metadata + title/abstract summary

References:
- Search guide: https://developers.openalex.org/guides/searching
- Paging guide: https://developers.openalex.org/guides/page-through-results
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


API_BASE_URL = "https://api.openalex.org"
DEFAULT_TIMEOUT = 45
DEFAULT_MAX_RETRIES = 4
DEFAULT_BACKOFF_SECONDS = 1.0


def normalize_doi(doi: str) -> str:
    d = (doi or "").strip()
    if d.lower().startswith("https://doi.org/"):
        d = d[16:]
    elif d.lower().startswith("http://doi.org/"):
        d = d[15:]
    elif d.lower().startswith("doi:"):
        d = d[4:]
    return d.strip().lower()


def slugify(s: str) -> str:
    out = re.sub(r"[^\w\-]+", "_", (s or "").strip())
    out = out.strip("_")
    return out[:80] or "query"


def reconstruct_abstract(abstract_inverted_index: dict) -> str:
    if not isinstance(abstract_inverted_index, dict) or not abstract_inverted_index:
        return ""
    position_word = {}
    for word, positions in abstract_inverted_index.items():
        if not isinstance(positions, list):
            continue
        for pos in positions:
            if isinstance(pos, int) and pos not in position_word:
                position_word[pos] = word
    if not position_word:
        return ""
    return " ".join(position_word[p] for p in sorted(position_word.keys()))


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

    if ext in {".txt"}:
        lines = []
        for line in path.read_text(encoding="utf-8").splitlines():
            x = line.strip()
            if not x or x.startswith("#"):
                continue
            lines.append(x)
        return unique_keep_order(lines)

    if ext in {".csv"}:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return []
            if query_column not in reader.fieldnames:
                raise ValueError(
                    f"CSV column '{query_column}' not found. Available columns: {reader.fieldnames}"
                )
            return unique_keep_order([(row.get(query_column) or "").strip() for row in reader])

    if ext in {".json"}:
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

    if ext in {".jsonl"}:
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


class OpenAlexSearchWrapper:
    def __init__(
        self,
        api_key: str = "",
        mailto: str = "",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    ):
        self.api_key = (api_key or "").strip()
        self.mailto = (mailto or "").strip()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = requests.Session()

    def _request_with_retry(self, url: str, params: dict) -> requests.Response:
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.get(url=url, params=params, timeout=self.timeout)
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
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

    def search_works(
        self,
        query: str,
        search_param: str,
        filter_str: str = "",
        sort: str = "",
        per_page: int = 100,
        max_results: int = 1000,
        select: str = "",
    ) -> dict:
        is_semantic = search_param == "search.semantic"
        page_size = max(1, min(50 if is_semantic else 100, per_page))
        params = {
            search_param: query,
            "per_page": page_size,
        }
        if not is_semantic:
            params["cursor"] = "*"
        else:
            params["page"] = 1
        if filter_str:
            params["filter"] = filter_str
        if sort:
            params["sort"] = sort
        if select:
            params["select"] = select
        if self.api_key:
            params["api_key"] = self.api_key
        if self.mailto:
            params["mailto"] = self.mailto

        url = f"{API_BASE_URL}/works"
        works = []
        calls = 0
        total_cost_usd = 0.0
        total_count_reported = None
        last_next_cursor = None

        # OpenAlex semantic search does not support cursor pagination and is limited to 50 results.
        target_max = min(max_results, 50) if is_semantic else max_results

        while len(works) < target_max:
            try:
                resp = self._request_with_retry(url=url, params=params)
            except Exception as e:
                return {
                    "success": False,
                    "status": f"error:{str(e)[:120]}",
                    "query": query,
                    "calls": calls,
                    "results": works,
                }

            calls += 1
            if resp.status_code >= 400:
                return {
                    "success": False,
                    "status": f"http_{resp.status_code}",
                    "error": (resp.text or "").strip().replace("\n", " ")[:240],
                    "query": query,
                    "calls": calls,
                    "results": works,
                }

            try:
                payload = resp.json()
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "status": "invalid_json",
                    "query": query,
                    "calls": calls,
                    "results": works,
                }

            meta = payload.get("meta", {}) or {}
            batch = payload.get("results", []) or []
            total_count_reported = meta.get("count", total_count_reported)
            last_next_cursor = meta.get("next_cursor")
            total_cost_usd += float(meta.get("cost_usd", 0.0) or 0.0)

            if not batch:
                break

            for w in batch:
                works.append(w)
                if len(works) >= max_results:
                    break

            if is_semantic:
                # Basic paging path for semantic mode.
                if len(batch) < page_size:
                    break
                params["page"] = int(params.get("page", 1)) + 1
            else:
                if not last_next_cursor:
                    break
                params["cursor"] = last_next_cursor

        return {
            "success": True,
            "status": "success",
            "query": query,
            "calls": calls,
            "results": works,
            "meta_count": total_count_reported,
            "next_cursor": last_next_cursor,
            "cost_usd_total": round(total_cost_usd, 8),
        }


def main():
    parser = argparse.ArgumentParser(description="OpenAlex query search wrapper for large metadata retrieval")
    parser.add_argument("--api-key", default=os.getenv("OPENALEX_API_KEY", ""), help="OpenAlex API key")
    parser.add_argument("--mailto", default=os.getenv("OPENALEX_MAILTO", ""), help="Contact email (recommended)")
    parser.add_argument("--query", action="append", default=[], help="OpenAlex query string (repeat allowed)")
    parser.add_argument("--query-file", default="", help="Query file: txt/csv/json/jsonl")
    parser.add_argument("--query-column", default="query", help="Query column in CSV/JSON object inputs")
    parser.add_argument(
        "--search-param",
        default="search",
        choices=["search", "search.exact", "search.semantic"],
        help="OpenAlex search parameter",
    )
    parser.add_argument("--filter", default="", help="OpenAlex filter string")
    parser.add_argument("--sort", default="", help="OpenAlex sort string, e.g. cited_by_count:desc")
    parser.add_argument("--select", default="", help="Optional root-level select fields")
    parser.add_argument("--per-page", type=int, default=100, help="Results per page (1-100)")
    parser.add_argument("--max-results-per-query", type=int, default=1000)
    parser.add_argument("--keep-duplicates", action="store_true", help="Keep duplicates across queries")
    parser.add_argument("--out-dir", default="openalex_search_outputs")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--backoff-seconds", type=float, default=DEFAULT_BACKOFF_SECONDS)
    args = parser.parse_args()

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

    summary_json = out_dir / "run_summary.json"
    summary_csv = out_dir / "works_summary.csv"
    full_jsonl = out_dir / "works_full.jsonl"

    client = OpenAlexSearchWrapper(
        api_key=args.api_key,
        mailto=args.mailto,
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
    )

    seen_ids = set()
    run_summary = []
    summary_rows = []
    total_written = 0

    with full_jsonl.open("w", encoding="utf-8") as jsonl_f:
        for idx, query in enumerate(tqdm(queries, desc="OpenAlex queries"), start=1):
            result = client.search_works(
                query=query,
                search_param=args.search_param,
                filter_str=args.filter,
                sort=args.sort,
                per_page=args.per_page,
                max_results=args.max_results_per_query,
                select=args.select,
            )

            query_slug = f"{idx:03d}_{slugify(query)}"
            query_raw_path = query_runs_dir / f"{query_slug}.json"
            query_raw_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

            row = {
                "query_index": idx,
                "query": query,
                "status": result.get("status"),
                "success": bool(result.get("success")),
                "calls": result.get("calls", 0),
                "meta_count": result.get("meta_count"),
                "cost_usd_total": result.get("cost_usd_total", 0),
                "returned_results": len(result.get("results", [])),
                "stored_results": 0,
                "raw_query_path": str(query_raw_path),
                "error": result.get("error", ""),
            }

            if result.get("success"):
                for work in result.get("results", []):
                    oa_id = work.get("id", "")
                    if not args.keep_duplicates and oa_id and oa_id in seen_ids:
                        continue
                    if oa_id:
                        seen_ids.add(oa_id)

                    doi = normalize_doi(work.get("doi", "") or "")
                    title = work.get("title") or work.get("display_name") or ""
                    abstract = reconstruct_abstract(work.get("abstract_inverted_index", {}))

                    summary_rows.append(
                        {
                            "query_index": idx,
                            "query": query,
                            "openalex_id": oa_id,
                            "doi": doi,
                            "title": title,
                            "abstract": abstract,
                            "publication_year": work.get("publication_year"),
                            "type": work.get("type"),
                            "cited_by_count": work.get("cited_by_count"),
                            "relevance_score": work.get("relevance_score", ""),
                            "is_oa": (work.get("open_access", {}) or {}).get("is_oa"),
                        }
                    )

                    jsonl_f.write(
                        json.dumps(
                            {
                                "query_index": idx,
                                "query": query,
                                "openalex_id": oa_id,
                                "doi": doi,
                                "title": title,
                                "abstract": abstract,
                                "work": work,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    total_written += 1
                    row["stored_results"] += 1

            run_summary.append(row)

    summary_json.write_text(json.dumps(run_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    cols = [
        "query_index",
        "query",
        "openalex_id",
        "doi",
        "title",
        "abstract",
        "publication_year",
        "type",
        "cited_by_count",
        "relevance_score",
        "is_oa",
    ]
    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in summary_rows:
            w.writerow({c: r.get(c, "") for c in cols})

    ok_queries = sum(1 for x in run_summary if x.get("success"))
    print(f"Done. queries={len(queries)}, success_queries={ok_queries}, failed_queries={len(queries)-ok_queries}")
    print(f"Stored unique works: {total_written}")
    print(f"Run summary: {summary_json}")
    print(f"Works summary CSV: {summary_csv}")
    print(f"Full metadata JSONL: {full_jsonl}")
    print(f"Per-query raw responses: {query_runs_dir}")


if __name__ == "__main__":
    main()
