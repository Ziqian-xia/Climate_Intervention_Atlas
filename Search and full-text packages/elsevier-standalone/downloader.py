#!/usr/bin/env python3
"""
Standalone Elsevier PDF downloader.

Inputs:
- API key (required): --api-key or env ELSEVIER_API_KEY
- DOI list (at least one source):
  1) repeat --doi
  2) --doi-file (csv/txt/json/jsonl), DOI can be one column

Outputs:
- PDFs in --out-dir/pdfs
- Run report JSON/CSV in --out-dir
"""

import argparse
import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import quote

import requests
from tqdm import tqdm


API_BASE_URL = "https://api.elsevier.com"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_RETRIES = 4
DEFAULT_BACKOFF_SECONDS = 1.0


def sanitize_filename(title: str, doi: str) -> str:
    doi_suffix = doi.split("/")[-1] if doi else "unknown"
    doi_suffix = re.sub(r"[^\w\-.]", "_", doi_suffix)
    clean_title = re.sub(r"[^\w\s\-]", "", title or "").strip()
    clean_title = clean_title[:80].replace(" ", "_") or "untitled"
    return f"{clean_title}_{doi_suffix}.pdf"


def normalize_doi(doi: str) -> str:
    """Normalize DOI for matching/deduplication."""
    d = (doi or "").strip()
    if d.lower().startswith("https://doi.org/"):
        d = d[16:]
    elif d.lower().startswith("http://doi.org/"):
        d = d[15:]
    elif d.lower().startswith("doi:"):
        d = d[4:]
    return d.strip().lower()


def is_elsevier_doi(doi: str) -> bool:
    d = normalize_doi(doi)
    return bool(d) and d.startswith("10.1016/")


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
            # Allow {"dois":[...]} or {"data":[{"doi":"..."}]}
            if "dois" in data and isinstance(data["dois"], list):
                return unique_keep_order([str(x) for x in data["dois"]])
            if "data" in data and isinstance(data["data"], list):
                return unique_keep_order([str(x.get(doi_column, "")) for x in data["data"] if isinstance(x, dict)])
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


class ElsevierStandaloneDownloader:
    def __init__(
        self,
        api_key: str,
        inst_token: str = "",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    ):
        self.api_key = api_key.strip()
        self.inst_token = (inst_token or "").strip()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = requests.Session()

    def _headers(self, accept: str) -> dict:
        h = {
            "X-ELS-APIKey": self.api_key,
            "Accept": accept,
        }
        if self.inst_token:
            h["X-ELS-Insttoken"] = self.inst_token
        return h

    def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: dict,
        allow_redirects: bool = True,
    ) -> requests.Response:
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=allow_redirects,
                )
                # Retry on throttling and transient server errors.
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

    def check_entitlement(self, doi: str) -> dict:
        doi = normalize_doi(doi)
        url = f"{API_BASE_URL}/content/article/entitlement/doi/{quote(doi, safe='')}"
        try:
            resp = self._request_with_retry(
                method="GET",
                url=url,
                headers=self._headers("application/json"),
                allow_redirects=True,
            )
            if resp.status_code >= 400:
                return {"ok": False, "status_code": resp.status_code, "entitled": None, "error": f"http_{resp.status_code}"}
            payload = resp.json()
            ent = payload.get("entitlement-response", {}).get("document-entitlement", {})
            return {
                "ok": True,
                "status_code": resp.status_code,
                "entitled": bool(ent.get("entitled")),
                "message": ent.get("message"),
            }
        except Exception as e:
            return {"ok": False, "status_code": None, "entitled": None, "error": str(e)[:120]}

    def download_pdf(self, doi: str, out_pdf: Path, title: str = "", check_entitlement: bool = False) -> dict:
        doi = normalize_doi(doi)
        entitlement = self.check_entitlement(doi) if check_entitlement else None
        url = f"{API_BASE_URL}/content/article/doi/{quote(doi, safe='')}"
        try:
            resp = self._request_with_retry(
                method="GET",
                url=url,
                headers=self._headers("application/pdf"),
                allow_redirects=True,
            )
            if resp.status_code >= 400:
                return {
                    "doi": doi,
                    "status": f"http_{resp.status_code}",
                    "success": False,
                    "entitlement": entitlement,
                }

            body = resp.content or b""
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "pdf" not in ctype and not body.startswith(b"%PDF-"):
                return {
                    "doi": doi,
                    "status": f"not_pdf:{ctype or 'unknown'}",
                    "success": False,
                    "entitlement": entitlement,
                }

            out_pdf.write_bytes(body)
            api_status = resp.headers.get("X-ELS-Status", "")
            limited = "limited to first page" in api_status.lower()
            return {
                "doi": doi,
                "status": "success_limited" if limited else "success",
                "success": True,
                "limited": limited,
                "api_status": api_status,
                "entitlement": entitlement,
                "pdf_path": str(out_pdf),
                "title": title,
            }
        except Exception as e:
            return {
                "doi": doi,
                "status": f"error:{str(e)[:120]}",
                "success": False,
                "entitlement": entitlement,
            }


def main():
    parser = argparse.ArgumentParser(description="Standalone Elsevier DOI PDF downloader")
    parser.add_argument("--api-key", default=os.getenv("ELSEVIER_API_KEY", ""), help="Elsevier API key")
    parser.add_argument("--inst-token", default=os.getenv("ELSEVIER_INST_TOKEN", ""), help="Elsevier institution token (optional)")
    parser.add_argument("--doi", action="append", default=[], help="DOI (repeat this arg for multiple)")
    parser.add_argument("--doi-file", default="", help="DOI file path: csv/txt/json/jsonl")
    parser.add_argument("--doi-column", default="doi", help="DOI column name in structured files (default: doi)")
    parser.add_argument("--title-column", default="title", help="Title column name in CSV/JSON list of objects")
    parser.add_argument("--out-dir", default="outputs", help="Output dir (default: outputs)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout seconds")
    parser.add_argument("--check-entitlement", action="store_true", help="Call entitlement API in addition to retrieval (extra API call)")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="Retry count for 429/5xx/network errors")
    parser.add_argument("--backoff-seconds", type=float, default=DEFAULT_BACKOFF_SECONDS, help="Initial exponential backoff in seconds")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing API key. Use --api-key or set ELSEVIER_API_KEY.")

    file_dois = []
    title_map = {}
    if args.doi_file:
        doi_path = Path(args.doi_file)
        if not doi_path.exists():
            raise SystemExit(f"DOI file not found: {doi_path}")

        if doi_path.suffix.lower() == ".csv":
            with open(doi_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                fields = reader.fieldnames or []
                if args.doi_column not in fields:
                    raise SystemExit(
                        f"CSV column '{args.doi_column}' not found. Available columns: {fields}"
                    )
                doi_field = args.doi_column
                for row in reader:
                    doi = normalize_doi((row.get(doi_field, "") or "").strip())
                    if doi:
                        file_dois.append(doi)
                        title_map[doi] = (row.get(args.title_column, "") or "").strip()
        else:
            file_dois = load_dois_from_file(doi_path, args.doi_column)

    dois = unique_keep_order([*args.doi, *file_dois])
    if not dois:
        raise SystemExit("No DOI provided. Use --doi and/or --doi-file.")

    out_dir = Path(args.out_dir)
    pdf_dir = out_dir / "pdfs"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    downloader = ElsevierStandaloneDownloader(
        api_key=args.api_key,
        inst_token=args.inst_token,
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
    )

    results = []
    for doi in tqdm(dois, desc="Elsevier download"):
        doi = normalize_doi(doi)
        title = title_map.get(doi, "")
        if not is_elsevier_doi(doi):
            results.append({
                "doi": doi,
                "status": "not_elsevier_doi",
                "success": False,
            })
            continue

        filename = sanitize_filename(title, doi)
        out_pdf = pdf_dir / filename
        if out_pdf.exists():
            results.append({
                "doi": doi,
                "status": "exists",
                "success": True,
                "pdf_path": str(out_pdf),
            })
            continue

        results.append(
            downloader.download_pdf(
                doi=doi,
                out_pdf=out_pdf,
                title=title,
                check_entitlement=args.check_entitlement,
            )
        )

    result_json = out_dir / "results.json"
    result_csv = out_dir / "results.csv"
    result_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_fields = [
        "doi",
        "status",
        "success",
        "limited",
        "api_status",
        "pdf_path",
        "title",
    ]
    with open(result_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in csv_fields})

    total = len(results)
    success = sum(1 for r in results if r.get("success"))
    limited = sum(1 for r in results if r.get("limited"))
    print(f"\nDone. total={total}, success={success}, limited={limited}")
    print(f"PDF dir: {pdf_dir}")
    print(f"Report: {result_json}")


if __name__ == "__main__":
    main()
