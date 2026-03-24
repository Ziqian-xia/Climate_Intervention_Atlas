#!/usr/bin/env python3
"""
Unified publisher downloader (Elsevier + Wiley).

Environment variables supported:
- ELSEVIER_API_KEY
- ELSEVIER_INST_TOKEN
- WILEY_TDM_CLIENT_TOKEN
"""

import argparse
import csv
import json
import os
from pathlib import Path

import requests

from downloader import (
    ElsevierStandaloneDownloader,
    is_elsevier_doi,
    normalize_doi,
    sanitize_filename,
    unique_keep_order,
)


WILEY_BASE_URL = "https://api.wiley.com/onlinelibrary/tdm/v1/articles/"


def is_wiley_doi(doi: str) -> bool:
    d = normalize_doi(doi)
    return d.startswith("10.1002/") or d.startswith("10.1111/")


def load_csv(path: Path, doi_col: str = "doi", title_col: str = "title") -> tuple[list[str], dict]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
    if not rows:
        return [], {}
    if doi_col not in rows[0]:
        raise SystemExit(f"CSV column '{doi_col}' not found. Available columns: {list(rows[0].keys())}")
    dois = []
    title_map = {}
    for row in rows:
        doi = normalize_doi((row.get(doi_col) or "").strip())
        if not doi:
            continue
        dois.append(doi)
        title_map[doi] = (row.get(title_col) or "").strip()
    return unique_keep_order(dois), title_map


def detect_publisher(doi: str) -> str:
    if is_elsevier_doi(doi):
        return "elsevier"
    if is_wiley_doi(doi):
        return "wiley"
    return "unknown"


def download_wiley(
    doi: str,
    out_pdf: Path,
    token: str,
    timeout: int = 60,
    max_retries: int = 2,
    backoff_seconds: float = 1.0,
) -> dict:
    if not token:
        return {"doi": doi, "status": "missing_wiley_token", "success": False}

    headers = {"Wiley-TDM-Client-Token": token}
    url = WILEY_BASE_URL + doi

    for attempt in range(max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                import time

                time.sleep(backoff_seconds * (2**attempt))
                continue

            if resp.status_code >= 400:
                return {
                    "doi": doi,
                    "status": f"http_{resp.status_code}",
                    "success": False,
                }
            body = resp.content or b""
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "pdf" not in ctype and not body.startswith(b"%PDF-"):
                return {
                    "doi": doi,
                    "status": f"not_pdf:{ctype or 'unknown'}",
                    "success": False,
                }
            out_pdf.write_bytes(body)
            return {
                "doi": doi,
                "status": "success",
                "success": True,
                "pdf_path": str(out_pdf),
            }
        except requests.RequestException as e:
            if attempt < max_retries:
                import time

                time.sleep(backoff_seconds * (2**attempt))
                continue
            return {"doi": doi, "status": f"error:{str(e)[:120]}", "success": False}

    return {"doi": doi, "status": "retry_exhausted", "success": False}


def main():
    parser = argparse.ArgumentParser(description="Unified Elsevier/Wiley downloader")
    parser.add_argument("--publisher", choices=["auto", "elsevier", "wiley"], default="auto")
    parser.add_argument("--doi", action="append", default=[])
    parser.add_argument("--doi-file", default="")
    parser.add_argument("--doi-column", default="doi")
    parser.add_argument("--title-column", default="title")
    parser.add_argument("--out-dir", default="publisher_outputs")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--backoff-seconds", type=float, default=1.0)
    parser.add_argument("--check-entitlement", action="store_true", help="Elsevier only")
    parser.add_argument("--elsevier-api-key", default=os.getenv("ELSEVIER_API_KEY", ""))
    parser.add_argument("--elsevier-inst-token", default=os.getenv("ELSEVIER_INST_TOKEN", ""))
    parser.add_argument("--wiley-token", default=os.getenv("WILEY_TDM_CLIENT_TOKEN", ""))
    args = parser.parse_args()

    title_map = {}
    file_dois = []
    if args.doi_file:
        csv_path = Path(args.doi_file).resolve()
        if not csv_path.exists():
            raise SystemExit(f"DOI file not found: {csv_path}")
        if csv_path.suffix.lower() != ".csv":
            raise SystemExit("For publisher_downloader, --doi-file currently supports CSV only.")
        file_dois, title_map = load_csv(csv_path, args.doi_column, args.title_column)

    dois = unique_keep_order([normalize_doi(x) for x in [*args.doi, *file_dois]])
    if not dois:
        raise SystemExit("No DOI provided. Use --doi and/or --doi-file.")

    out_dir = Path(args.out_dir).resolve()
    pdf_dir = out_dir / "pdfs"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    elsevier = ElsevierStandaloneDownloader(
        api_key=args.elsevier_api_key,
        inst_token=args.elsevier_inst_token,
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
    )

    results = []
    for doi in dois:
        pub = args.publisher if args.publisher != "auto" else detect_publisher(doi)
        title = title_map.get(doi, "")
        out_pdf = pdf_dir / sanitize_filename(title, doi)
        if out_pdf.exists():
            results.append({"doi": doi, "publisher": pub, "status": "exists", "success": True, "pdf_path": str(out_pdf)})
            continue

        if pub == "elsevier":
            if not args.elsevier_api_key:
                results.append({"doi": doi, "publisher": pub, "status": "missing_elsevier_api_key", "success": False})
            else:
                r = elsevier.download_pdf(doi=doi, out_pdf=out_pdf, title=title, check_entitlement=args.check_entitlement)
                r["publisher"] = "elsevier"
                results.append(r)
            continue

        if pub == "wiley":
            r = download_wiley(
                doi=doi,
                out_pdf=out_pdf,
                token=args.wiley_token,
                timeout=args.timeout,
                max_retries=max(0, min(args.max_retries, 4)),
                backoff_seconds=args.backoff_seconds,
            )
            r["publisher"] = "wiley"
            results.append(r)
            continue

        results.append({"doi": doi, "publisher": "unknown", "status": "unsupported_publisher", "success": False})

    out_json = out_dir / "results.json"
    out_csv = out_dir / "results.csv"
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    cols = ["doi", "publisher", "status", "success", "pdf_path", "api_status"]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in results:
            w.writerow({c: r.get(c, "") for c in cols})

    total = len(results)
    success = sum(1 for r in results if r.get("success"))
    print(f"Done. total={total}, success={success}, failed={total-success}")
    print(f"PDF dir: {pdf_dir}")
    print(f"Report: {out_json}")


if __name__ == "__main__":
    main()
