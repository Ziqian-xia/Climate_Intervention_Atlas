#!/usr/bin/env python3
"""
Standalone OpenAlex metadata wrapper.

Goal:
- Fetch full work metadata from OpenAlex by DOI (single or batch)
- Export complete metadata plus easy-to-use title/abstract summaries

Outputs:
- out_dir/results.json        (summary records)
- out_dir/results.csv         (summary table)
- out_dir/metadata_full.jsonl (full work metadata, one JSON object per line)
- out_dir/raw_works/*.json    (one full metadata JSON per DOI)
"""

import argparse
import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

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


def unique_keep_order(items: Iterable[str]) -> list[str]:
    out = []
    seen = set()
    for item in items:
        k = normalize_doi(item or "")
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out


def safe_filename_from_doi(doi: str) -> str:
    return re.sub(r"[^\w\-.]", "_", normalize_doi(doi)) or "unknown_doi"


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


def load_dois_from_file(path: Path, doi_column: str) -> list[str]:
    ext = path.suffix.lower()

    if ext in {".txt"}:
        return unique_keep_order(path.read_text(encoding="utf-8").splitlines())

    if ext in {".csv"}:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return []
            if doi_column not in reader.fieldnames:
                raise ValueError(
                    f"CSV column '{doi_column}' not found. Available columns: {reader.fieldnames}"
                )
            return unique_keep_order([row.get(doi_column, "") for row in reader])

    if ext in {".json"}:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                return unique_keep_order([str(x.get(doi_column, "")) for x in data])
            return unique_keep_order([str(x) for x in data])
        if isinstance(data, dict):
            if "dois" in data and isinstance(data["dois"], list):
                return unique_keep_order([str(x) for x in data["dois"]])
            if "data" in data and isinstance(data["data"], list):
                return unique_keep_order(
                    [str(x.get(doi_column, "")) for x in data["data"] if isinstance(x, dict)]
                )
        return []

    if ext in {".jsonl"}:
        dois = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, dict):
                dois.append(str(obj.get(doi_column, "")))
            else:
                dois.append(str(obj))
        return unique_keep_order(dois)

    raise ValueError(f"Unsupported file type: {ext}. Use csv/txt/json/jsonl.")


class OpenAlexMetadataWrapper:
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
                # retry 429 and transient 5xx
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

    def fetch_work_by_doi(self, doi: str) -> dict:
        doi_norm = normalize_doi(doi)
        if not doi_norm:
            return {
                "doi": doi,
                "status": "invalid_doi",
                "success": False,
            }

        # OpenAlex supports external IDs in URN form, e.g. doi:10.1234/example
        external_id = f"doi:{doi_norm}"
        url = f"{API_BASE_URL}/works/{quote(external_id, safe='')}"

        params = {}
        if self.api_key:
            params["api_key"] = self.api_key
        if self.mailto:
            params["mailto"] = self.mailto

        try:
            resp = self._request_with_retry(url=url, params=params)
        except Exception as e:
            return {
                "doi": doi_norm,
                "status": f"error:{str(e)[:120]}",
                "success": False,
            }

        if resp.status_code >= 400:
            msg = (resp.text or "").strip().replace("\n", " ")[:240]
            return {
                "doi": doi_norm,
                "status": f"http_{resp.status_code}",
                "success": False,
                "error": msg,
            }

        try:
            work = resp.json()
        except json.JSONDecodeError:
            return {
                "doi": doi_norm,
                "status": "invalid_json",
                "success": False,
            }

        abstract = reconstruct_abstract(work.get("abstract_inverted_index", {}))
        title = work.get("title") or work.get("display_name") or ""

        return {
            "doi": doi_norm,
            "status": "success",
            "success": True,
            "openalex_id": work.get("id", ""),
            "title": title,
            "abstract": abstract,
            "publication_year": work.get("publication_year"),
            "type": work.get("type"),
            "cited_by_count": work.get("cited_by_count"),
            "work": work,
        }


def main():
    parser = argparse.ArgumentParser(description="OpenAlex metadata wrapper (DOI -> full metadata)")
    parser.add_argument("--api-key", default=os.getenv("OPENALEX_API_KEY", ""), help="OpenAlex API key (recommended)")
    parser.add_argument("--mailto", default=os.getenv("OPENALEX_MAILTO", ""), help="Contact email for polite pool")
    parser.add_argument("--doi", action="append", default=[], help="DOI (repeat for multiple)")
    parser.add_argument("--doi-file", default="", help="DOI file: csv/txt/json/jsonl")
    parser.add_argument("--doi-column", default="doi", help="DOI column for CSV/JSON object inputs")
    parser.add_argument("--out-dir", default="openalex_outputs")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--backoff-seconds", type=float, default=DEFAULT_BACKOFF_SECONDS)
    args = parser.parse_args()

    file_dois = []
    if args.doi_file:
        p = Path(args.doi_file).resolve()
        if not p.exists():
            raise SystemExit(f"DOI file not found: {p}")
        file_dois = load_dois_from_file(p, args.doi_column)

    dois = unique_keep_order([*args.doi, *file_dois])
    if not dois:
        raise SystemExit("No DOI provided. Use --doi and/or --doi-file.")

    out_dir = Path(args.out_dir).resolve()
    raw_dir = out_dir / "raw_works"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    client = OpenAlexMetadataWrapper(
        api_key=args.api_key,
        mailto=args.mailto,
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
    )

    out_json = out_dir / "results.json"
    out_csv = out_dir / "results.csv"
    out_jsonl = out_dir / "metadata_full.jsonl"
    results = []
    with out_jsonl.open("w", encoding="utf-8") as jsonl_f:
        for doi in tqdm(dois, desc="OpenAlex fetch"):
            r = client.fetch_work_by_doi(doi)
            if r.get("success"):
                doi_norm = r["doi"]
                work = r.pop("work")
                raw_path = raw_dir / f"{safe_filename_from_doi(doi_norm)}.json"
                raw_path.write_text(json.dumps(work, ensure_ascii=False, indent=2), encoding="utf-8")
                r["raw_path"] = str(raw_path)
                jsonl_f.write(
                    json.dumps(
                        {
                            "query_doi": doi_norm,
                            "openalex_id": work.get("id"),
                            "title": r.get("title", ""),
                            "abstract": r.get("abstract", ""),
                            "work": work,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            results.append(r)

    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    cols = [
        "doi",
        "status",
        "success",
        "openalex_id",
        "publication_year",
        "type",
        "cited_by_count",
        "title",
        "abstract",
        "raw_path",
        "error",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in results:
            row = {c: r.get(c, "") for c in cols}
            w.writerow(row)

    total = len(results)
    success = sum(1 for r in results if r.get("success"))
    print(f"Done. total={total}, success={success}, failed={total-success}")
    print(f"Output dir: {out_dir}")
    print(f"Summary JSON: {out_json}")
    print(f"Summary CSV: {out_csv}")
    print(f"Full metadata JSONL: {out_jsonl}")
    print(f"Per-work raw JSON dir: {raw_dir}")


if __name__ == "__main__":
    main()
