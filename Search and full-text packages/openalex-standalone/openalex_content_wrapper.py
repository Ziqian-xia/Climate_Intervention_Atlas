#!/usr/bin/env python3
"""
OpenAlex content wrapper (workflow step-3):
- Input: OpenAlex work IDs and/or DOIs
- Download: PDF and/or TEI XML (grobid-xml) from content.openalex.org
- Output: files + structured download report
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


METADATA_API_BASE_URL = "https://api.openalex.org"
CONTENT_API_BASE_URL = "https://content.openalex.org/works"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_RETRIES = 4
DEFAULT_BACKOFF_SECONDS = 1.0
CONTENT_PRICE_PER_FILE_USD = 0.01


def normalize_doi(doi: str) -> str:
    d = (doi or "").strip()
    if d.lower().startswith("https://doi.org/"):
        d = d[16:]
    elif d.lower().startswith("http://doi.org/"):
        d = d[15:]
    elif d.lower().startswith("doi:"):
        d = d[4:]
    return d.strip().lower()


def normalize_work_id(x: str) -> str:
    s = (x or "").strip()
    s = re.sub(r"^https?://openalex\.org/", "", s, flags=re.IGNORECASE)
    s = s.strip()
    if not s:
        return ""
    if re.fullmatch(r"[Ww]\d+", s):
        return "W" + s[1:]
    return s


def is_probable_work_id(x: str) -> bool:
    return bool(re.fullmatch(r"[Ww]\d+", (x or "").strip()))


def unique_keep_order(items: Iterable[str]) -> list[str]:
    out = []
    seen = set()
    for item in items:
        k = (item or "").strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out


def safe_name(x: str) -> str:
    return re.sub(r"[^\w\-.]", "_", (x or "").strip()) or "unknown"


def parse_content_types(raw: str) -> list[str]:
    aliases = {
        "pdf": "pdf",
        "xml": "grobid_xml",
        "grobid_xml": "grobid_xml",
        "grobid-xml": "grobid_xml",
    }
    parts = [p.strip().lower() for p in (raw or "").split(",") if p.strip()]
    out = []
    for p in parts:
        if p not in aliases:
            raise ValueError(f"Unsupported content type: {p}. Use pdf, xml, grobid_xml.")
        k = aliases[p]
        if k not in out:
            out.append(k)
    return out or ["pdf"]


def read_rows_from_file(path: Path) -> list[dict]:
    ext = path.suffix.lower()
    if ext == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    if ext == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                return data
            return [{"value": x} for x in data]
        if isinstance(data, dict):
            if isinstance(data.get("data"), list):
                return [x for x in data["data"] if isinstance(x, dict)]
            if isinstance(data.get("items"), list):
                return [x for x in data["items"] if isinstance(x, dict)]
            return [data]
    if ext == ".jsonl":
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
            else:
                rows.append({"value": obj})
        return rows
    if ext == ".txt":
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            x = line.strip()
            if not x or x.startswith("#"):
                continue
            rows.append({"value": x})
        return rows
    raise ValueError(f"Unsupported id file type: {ext}. Use csv/txt/json/jsonl.")


def collect_targets(
    work_ids: list[str],
    dois: list[str],
    id_file: str,
    work_id_column: str,
    doi_column: str,
    from_works_summary: str,
) -> tuple[list[str], list[str]]:
    work_pool = [normalize_work_id(x) for x in work_ids]
    doi_pool = [normalize_doi(x) for x in dois]

    if id_file:
        rows = read_rows_from_file(Path(id_file).resolve())
        for row in rows:
            if work_id_column in row and str(row.get(work_id_column, "")).strip():
                work_pool.append(normalize_work_id(str(row.get(work_id_column, ""))))
            if doi_column in row and str(row.get(doi_column, "")).strip():
                doi_pool.append(normalize_doi(str(row.get(doi_column, ""))))
            if "value" in row:
                v = str(row["value"]).strip()
                if is_probable_work_id(v) or v.lower().startswith("https://openalex.org/w"):
                    work_pool.append(normalize_work_id(v))
                else:
                    doi_pool.append(normalize_doi(v))

    if from_works_summary:
        rows = read_rows_from_file(Path(from_works_summary).resolve())
        for row in rows:
            oa = str(row.get("openalex_id", "")).strip()
            d = str(row.get("doi", "")).strip()
            # Prefer openalex_id from step-2 outputs. Only fall back to DOI when ID is missing.
            if oa:
                work_pool.append(normalize_work_id(oa))
            elif d:
                doi_pool.append(normalize_doi(d))

    work_ids_final = unique_keep_order([x for x in work_pool if x])
    dois_final = unique_keep_order([x for x in doi_pool if x])
    return work_ids_final, dois_final


class OpenAlexContentWrapper:
    def __init__(
        self,
        api_key: str,
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

    def _request_with_retry(
        self,
        url: str,
        params: Optional[dict] = None,
        stream: bool = False,
    ) -> requests.Response:
        params = params or {}
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.get(url=url, params=params, timeout=self.timeout, stream=stream, allow_redirects=True)
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

    def fetch_work_by_id(self, work_id: str) -> dict:
        wid = normalize_work_id(work_id)
        url = f"{METADATA_API_BASE_URL}/works/{quote(wid, safe='')}"
        params = {}
        if self.api_key:
            params["api_key"] = self.api_key
        if self.mailto:
            params["mailto"] = self.mailto
        resp = self._request_with_retry(url=url, params=params)
        if resp.status_code >= 400:
            return {
                "ok": False,
                "status": f"http_{resp.status_code}",
                "error": (resp.text or "").strip().replace("\n", " ")[:240],
                "work_id": wid,
            }
        return {"ok": True, "status": "success", "work": resp.json(), "work_id": wid}

    def fetch_work_by_doi(self, doi: str) -> dict:
        d = normalize_doi(doi)
        external = f"doi:{d}"
        url = f"{METADATA_API_BASE_URL}/works/{quote(external, safe='')}"
        params = {}
        if self.api_key:
            params["api_key"] = self.api_key
        if self.mailto:
            params["mailto"] = self.mailto
        resp = self._request_with_retry(url=url, params=params)
        if resp.status_code >= 400:
            return {
                "ok": False,
                "status": f"http_{resp.status_code}",
                "error": (resp.text or "").strip().replace("\n", " ")[:240],
                "doi": d,
            }
        work = resp.json()
        return {"ok": True, "status": "success", "work": work, "doi": d}

    def download_content(self, work_id: str, content_type: str, out_file: Path) -> dict:
        if content_type == "pdf":
            suffix = ".pdf"
        elif content_type == "grobid_xml":
            suffix = ".grobid-xml"
        else:
            return {"ok": False, "status": "invalid_content_type", "http_status": None}

        params = {"api_key": self.api_key}
        url = f"{CONTENT_API_BASE_URL}/{quote(work_id, safe='')}{suffix}"

        try:
            resp = self._request_with_retry(url=url, params=params, stream=True)
        except Exception as e:
            return {"ok": False, "status": f"error:{str(e)[:120]}", "http_status": None}

        ctype = (resp.headers.get("Content-Type") or "").lower()
        if resp.status_code >= 400:
            msg = ""
            try:
                msg = resp.text[:240].replace("\n", " ")
            except Exception:
                msg = ""
            return {
                "ok": False,
                "status": f"http_{resp.status_code}",
                "http_status": resp.status_code,
                "content_type": ctype,
                "error": msg,
            }

        out_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = out_file.with_suffix(out_file.suffix + ".part")
        bytes_written = 0
        first_bytes = b""
        with tmp.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                if not first_bytes:
                    first_bytes = chunk[:1024]
                f.write(chunk)
                bytes_written += len(chunk)

        first_strip = first_bytes.lstrip()
        is_pdf_magic = first_bytes.startswith(b"%PDF-")
        is_gzip_magic = first_bytes.startswith(b"\x1f\x8b")
        is_xml_magic = first_strip.startswith(b"<?xml") or first_strip.startswith(b"<")

        if content_type == "pdf":
            if not is_pdf_magic:
                tmp.unlink(missing_ok=True)
                return {
                    "ok": False,
                    "status": f"not_pdf:{ctype or 'unknown'}",
                    "http_status": resp.status_code,
                    "content_type": ctype,
                }
            final_path = out_file
        else:
            # OpenAlex may return TEI XML as plain XML or gzip-compressed XML
            if not (is_xml_magic or is_gzip_magic):
                tmp.unlink(missing_ok=True)
                return {
                    "ok": False,
                    "status": f"not_xml:{ctype or 'unknown'}",
                    "http_status": resp.status_code,
                    "content_type": ctype,
                }
            final_path = out_file.with_suffix(out_file.suffix + ".gz") if is_gzip_magic else out_file

        tmp.replace(final_path)

        return {
            "ok": True,
            "status": "success",
            "http_status": resp.status_code,
            "content_type": ctype,
            "bytes": bytes_written,
            "file_path": str(final_path),
        }


def main():
    parser = argparse.ArgumentParser(description="OpenAlex content downloader (PDF/TEI XML)")
    parser.add_argument("--api-key", default=os.getenv("OPENALEX_API_KEY", ""), help="OpenAlex API key (required for content API)")
    parser.add_argument("--mailto", default=os.getenv("OPENALEX_MAILTO", ""), help="Optional email for metadata API requests")
    parser.add_argument("--work-id", action="append", default=[], help="OpenAlex work ID, e.g. W4383823379")
    parser.add_argument("--doi", action="append", default=[], help="DOI (wrapper will resolve to work ID)")
    parser.add_argument("--id-file", default="", help="Input file with IDs: csv/txt/json/jsonl")
    parser.add_argument("--work-id-column", default="openalex_id", help="Work ID column in input file")
    parser.add_argument("--doi-column", default="doi", help="DOI column in input file")
    parser.add_argument(
        "--from-works-summary",
        default="",
        help="Path to works_summary.csv from openalex_search_wrapper (auto reads openalex_id + doi)",
    )
    parser.add_argument(
        "--content-types",
        default="pdf",
        help="Comma-separated: pdf,xml,grobid_xml (default: pdf)",
    )
    parser.add_argument("--max-targets", type=int, default=0, help="Optional cap on number of works (0 means no cap)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip files already downloaded")
    parser.add_argument("--out-dir", default="openalex_content_outputs")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--backoff-seconds", type=float, default=DEFAULT_BACKOFF_SECONDS)
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing API key. Use --api-key or OPENALEX_API_KEY.")

    requested_types = parse_content_types(args.content_types)
    work_ids, dois = collect_targets(
        work_ids=args.work_id,
        dois=args.doi,
        id_file=args.id_file,
        work_id_column=args.work_id_column,
        doi_column=args.doi_column,
        from_works_summary=args.from_works_summary,
    )

    if not work_ids and not dois:
        raise SystemExit("No targets provided. Use --work-id/--doi/--id-file/--from-works-summary.")

    # Apply target cap before DOI resolution to avoid unnecessary metadata calls.
    if args.max_targets and args.max_targets > 0:
        max_t = args.max_targets
        if len(work_ids) >= max_t:
            work_ids = work_ids[:max_t]
            dois = []
        else:
            need = max_t - len(work_ids)
            dois = dois[:need]

    out_dir = Path(args.out_dir).resolve()
    files_dir = out_dir / "files"
    raw_meta_dir = out_dir / "raw_work_metadata"
    out_dir.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)
    raw_meta_dir.mkdir(parents=True, exist_ok=True)

    client = OpenAlexContentWrapper(
        api_key=args.api_key,
        mailto=args.mailto,
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
    )

    # Build unique work map from explicit work IDs + DOI resolution.
    work_map = {}
    for wid in work_ids:
        wid_n = normalize_work_id(wid)
        if wid_n and wid_n not in work_map:
            work_map[wid_n] = {"work_id": wid_n, "doi_query": "", "doi": ""}

    for doi in tqdm(dois, desc="Resolve DOI -> work_id"):
        resolved = client.fetch_work_by_doi(doi)
        if not resolved.get("ok"):
            work_map[f"doi_unresolved:{doi}"] = {
                "work_id": "",
                "doi_query": doi,
                "doi": doi,
                "resolve_status": resolved.get("status", "error"),
                "resolve_error": resolved.get("error", ""),
            }
            continue
        w = resolved["work"]
        wid = normalize_work_id((w.get("id", "") or "").replace("https://openalex.org/", ""))
        if wid and wid not in work_map:
            work_map[wid] = {
                "work_id": wid,
                "doi_query": doi,
                "doi": normalize_doi(w.get("doi", "") or doi),
            }

    # Keep only valid work IDs for download flow
    work_items = [v for v in work_map.values() if v.get("work_id")]
    if args.max_targets and args.max_targets > 0:
        work_items = work_items[: args.max_targets]

    results = []
    attempts = 0
    success_files = 0

    for item in tqdm(work_items, desc="Download content by work"):
        wid = item["work_id"]
        meta_resp = client.fetch_work_by_id(wid)
        if not meta_resp.get("ok"):
            for ctype in requested_types:
                results.append(
                    {
                        "work_id": wid,
                        "doi": item.get("doi", ""),
                        "content_type": ctype,
                        "status": f"metadata_{meta_resp.get('status', 'error')}",
                        "success": False,
                        "http_status": "",
                        "file_path": "",
                        "bytes": 0,
                        "license": "",
                        "oa_status": "",
                        "is_oa": "",
                        "has_content_flag": "",
                        "error": meta_resp.get("error", ""),
                    }
                )
            continue

        work = meta_resp["work"]
        doi = normalize_doi(work.get("doi", "") or item.get("doi", ""))
        has_content = work.get("has_content", {}) or {}
        open_access = work.get("open_access", {}) or {}
        best_loc = work.get("best_oa_location", {}) or {}
        lic = best_loc.get("license", "")
        oa_status = open_access.get("oa_status", "")
        is_oa = open_access.get("is_oa", "")

        # Save metadata copy for traceability
        raw_meta_path = raw_meta_dir / f"{safe_name(wid)}.json"
        raw_meta_path.write_text(json.dumps(work, ensure_ascii=False, indent=2), encoding="utf-8")

        for ctype in requested_types:
            has_flag = bool(has_content.get("pdf")) if ctype == "pdf" else bool(has_content.get("grobid_xml"))
            subdir = "pdf" if ctype == "pdf" else "grobid_xml"
            ext = ".pdf" if ctype == "pdf" else ".xml"
            filename = f"{safe_name(wid)}{ext}"
            out_file = files_dir / subdir / filename

            if args.skip_existing and out_file.exists():
                results.append(
                    {
                        "work_id": wid,
                        "doi": doi,
                        "content_type": ctype,
                        "status": "exists",
                        "success": True,
                        "http_status": "",
                        "file_path": str(out_file),
                        "bytes": out_file.stat().st_size,
                        "license": lic,
                        "oa_status": oa_status,
                        "is_oa": is_oa,
                        "has_content_flag": has_flag,
                        "error": "",
                    }
                )
                continue

            if not has_flag:
                results.append(
                    {
                        "work_id": wid,
                        "doi": doi,
                        "content_type": ctype,
                        "status": "no_content_flag",
                        "success": False,
                        "http_status": "",
                        "file_path": "",
                        "bytes": 0,
                        "license": lic,
                        "oa_status": oa_status,
                        "is_oa": is_oa,
                        "has_content_flag": has_flag,
                        "error": "",
                    }
                )
                continue

            attempts += 1
            dl = client.download_content(wid, ctype, out_file)
            ok = bool(dl.get("ok"))
            if ok:
                success_files += 1
            results.append(
                {
                    "work_id": wid,
                    "doi": doi,
                    "content_type": ctype,
                    "status": dl.get("status", "error"),
                    "success": ok,
                    "http_status": dl.get("http_status", ""),
                    "file_path": dl.get("file_path", ""),
                    "bytes": dl.get("bytes", 0),
                    "license": lic,
                    "oa_status": oa_status,
                    "is_oa": is_oa,
                    "has_content_flag": has_flag,
                    "error": dl.get("error", ""),
                }
            )

    # append unresolved DOI rows
    for k, v in work_map.items():
        if not k.startswith("doi_unresolved:"):
            continue
        for ctype in requested_types:
            results.append(
                {
                    "work_id": "",
                    "doi": v.get("doi", ""),
                    "content_type": ctype,
                    "status": f"doi_unresolved_{v.get('resolve_status', 'error')}",
                    "success": False,
                    "http_status": "",
                    "file_path": "",
                    "bytes": 0,
                    "license": "",
                    "oa_status": "",
                    "is_oa": "",
                    "has_content_flag": "",
                    "error": v.get("resolve_error", ""),
                }
            )

    out_json = out_dir / "results.json"
    out_csv = out_dir / "results.csv"
    summary_json = out_dir / "run_summary.json"

    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    cols = [
        "work_id",
        "doi",
        "content_type",
        "status",
        "success",
        "http_status",
        "file_path",
        "bytes",
        "license",
        "oa_status",
        "is_oa",
        "has_content_flag",
        "error",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in results:
            w.writerow({c: r.get(c, "") for c in cols})

    summary = {
        "requested_work_ids": len(work_ids),
        "requested_dois": len(dois),
        "resolved_work_targets": len(work_items),
        "requested_content_types": requested_types,
        "download_attempts": attempts,
        "successful_downloads": success_files,
        "failed_downloads": attempts - success_files,
        "estimated_cost_usd_by_attempts": round(attempts * CONTENT_PRICE_PER_FILE_USD, 4),
        "estimated_cost_usd_by_successes": round(success_files * CONTENT_PRICE_PER_FILE_USD, 4),
        "price_per_content_file_usd": CONTENT_PRICE_PER_FILE_USD,
        "results_json": str(out_json),
        "results_csv": str(out_csv),
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        "Done. "
        f"targets={len(work_items)}, attempts={attempts}, "
        f"success={success_files}, failed={attempts-success_files}"
    )
    print(f"Output dir: {out_dir}")
    print(f"Run summary: {summary_json}")
    print(f"Results CSV: {out_csv}")


if __name__ == "__main__":
    main()
