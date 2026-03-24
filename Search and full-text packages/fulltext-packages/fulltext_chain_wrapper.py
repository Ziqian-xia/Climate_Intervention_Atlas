#!/usr/bin/env python3
"""
Validated full-text retrieval chain:
1) OpenAlex content API (OA-first, PDF)
2) Publisher APIs (Wiley PDF, Elsevier XML)
4) Playwright fallback (optional; PDF)

Optional conversion to Markdown:
- XML -> Markdown (built-in lightweight extractor)
- PDF -> Markdown (MinerU if available)
"""

import argparse
import csv
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import quote, urljoin

import requests
from tqdm import tqdm


DEFAULT_TIMEOUT = 60
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

ELSEVIER_BASE_URL = "https://api.elsevier.com/content/article/doi"
WILEY_BASE_URL = "https://api.wiley.com/onlinelibrary/tdm/v1/articles"
OPENALEX_META_BASE_URL = "https://api.openalex.org/works"
OPENALEX_CONTENT_BASE_URL = "https://content.openalex.org/works"


def normalize_doi(doi: str) -> str:
    d = (doi or "").strip()
    if d.lower().startswith("https://doi.org/"):
        d = d[16:]
    elif d.lower().startswith("http://doi.org/"):
        d = d[15:]
    elif d.lower().startswith("doi:"):
        d = d[4:]
    return d.strip().lower()


def is_elsevier_doi(doi: str) -> bool:
    return normalize_doi(doi).startswith("10.1016/")


def is_wiley_doi(doi: str) -> bool:
    d = normalize_doi(doi)
    return d.startswith("10.1002/") or d.startswith("10.1111/")


def safe_filename(title: str, doi: str, suffix: str = ".pdf") -> str:
    doi_suffix = normalize_doi(doi).split("/")[-1] if doi else "unknown"
    doi_suffix = re.sub(r"[^\w\-.]", "_", doi_suffix)
    clean_title = re.sub(r"[^\w\s\-]", "", (title or "")).strip()
    clean_title = clean_title[:80].replace(" ", "_") or "untitled"
    return f"{clean_title}_{doi_suffix}{suffix}"


def is_pdf_bytes(body: bytes) -> bool:
    return bool(body) and body.startswith(b"%PDF-") and len(body) > 1000


def is_xml_bytes(body: bytes) -> bool:
    if not body:
        return False
    head = body.lstrip()[:200].lower()
    return head.startswith(b"<") and (
        b"<?xml" in head
        or b"<xocs:" in head
        or b"<full-text-retrieval-response" in head
        or b"<article" in head
    )


def unique_keep_order(items: Iterable[dict]) -> list[dict]:
    out = []
    seen = set()
    for item in items:
        doi = normalize_doi(item.get("doi", ""))
        if not doi or doi in seen:
            continue
        seen.add(doi)
        out.append({**item, "doi": doi})
    return out


def load_records_from_file(path: Path, doi_column: str, title_column: str, journal_column: str) -> list[dict]:
    ext = path.suffix.lower()

    if ext == ".txt":
        out = []
        for line in path.read_text(encoding="utf-8").splitlines():
            x = line.strip()
            if not x or x.startswith("#"):
                continue
            out.append({"doi": x, "title": "", "journal": ""})
        return unique_keep_order(out)

    if ext == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return []
            if doi_column not in reader.fieldnames:
                raise ValueError(f"CSV column '{doi_column}' not found: {reader.fieldnames}")
            out = []
            for row in reader:
                out.append(
                    {
                        "doi": (row.get(doi_column) or "").strip(),
                        "title": (row.get(title_column) or "").strip(),
                        "journal": (row.get(journal_column) or "").strip(),
                    }
                )
            return unique_keep_order(out)

    if ext == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        out = []
        if isinstance(data, list):
            for x in data:
                if isinstance(x, dict):
                    out.append(
                        {
                            "doi": (x.get(doi_column) or x.get("doi") or "").strip(),
                            "title": (x.get(title_column) or x.get("title") or "").strip(),
                            "journal": (x.get(journal_column) or x.get("journal") or "").strip(),
                        }
                    )
                else:
                    out.append({"doi": str(x).strip(), "title": "", "journal": ""})
        elif isinstance(data, dict):
            seq = data.get("dois") if isinstance(data.get("dois"), list) else data.get("data")
            if isinstance(seq, list):
                for x in seq:
                    if isinstance(x, dict):
                        out.append(
                            {
                                "doi": (x.get(doi_column) or x.get("doi") or "").strip(),
                                "title": (x.get(title_column) or x.get("title") or "").strip(),
                                "journal": (x.get(journal_column) or x.get("journal") or "").strip(),
                            }
                        )
                    else:
                        out.append({"doi": str(x).strip(), "title": "", "journal": ""})
        return unique_keep_order(out)

    if ext == ".jsonl":
        out = []
        for line in path.read_text(encoding="utf-8").splitlines():
            x = line.strip()
            if not x:
                continue
            obj = json.loads(x)
            if isinstance(obj, dict):
                out.append(
                    {
                        "doi": (obj.get(doi_column) or obj.get("doi") or "").strip(),
                        "title": (obj.get(title_column) or obj.get("title") or "").strip(),
                        "journal": (obj.get(journal_column) or obj.get("journal") or "").strip(),
                    }
                )
            else:
                out.append({"doi": str(obj).strip(), "title": "", "journal": ""})
        return unique_keep_order(out)

    raise ValueError(f"Unsupported DOI file type: {ext}. Use txt/csv/json/jsonl.")


@dataclass
class AttemptResult:
    source: str
    status: str
    success: bool
    download_path: str = ""
    download_type: str = ""
    pdf_path: str = ""
    md_path: str = ""
    md_status: str = ""
    limited: bool = False
    http_status: Optional[int] = None
    api_status: str = ""
    detail: str = ""
    bytes_size: int = 0


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1].lower() if "}" in tag else tag.lower()


def xml_to_markdown(xml_path: Path, md_path: Path) -> tuple[str, str]:
    """
    Convert Elsevier XML to lightweight markdown.
    Returns (md_path, status).
    """
    try:
        raw = xml_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return "", f"xml_read_error:{str(e)[:120]}"

    title = ""
    paragraphs = []
    seen = set()

    try:
        root = ET.fromstring(raw)

        for elem in root.iter():
            lname = _local_name(elem.tag)
            if not title and lname in {"title", "article-title"}:
                t = " ".join(elem.itertext()).strip()
                if t and len(t) > 3:
                    title = t

        para_tags = {"para", "p", "simple-para", "abstract", "abstract-sec", "ce:para"}
        for elem in root.iter():
            lname = _local_name(elem.tag)
            if lname in para_tags or lname.endswith("para"):
                txt = " ".join(elem.itertext()).strip()
                txt = re.sub(r"\s+", " ", txt)
                if len(txt) < 20:
                    continue
                if txt in seen:
                    continue
                seen.add(txt)
                paragraphs.append(txt)
    except Exception:
        cleaned = re.sub(r"<[^>]+>", " ", raw)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            paragraphs = [cleaned[:20000]]

    if not title:
        title = xml_path.stem

    md_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", "", f"- Source XML: `{xml_path}`", ""]
    if paragraphs:
        lines.append("## Extracted Text")
        lines.append("")
        for p in paragraphs[:400]:
            lines.append(p)
            lines.append("")
    else:
        lines.extend(["## Extracted Text", "", "(No textual paragraphs extracted.)", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return str(md_path), "success"


def _detect_mineru_cmd() -> list[str]:
    venv_cli = Path(sys.executable).parent / "mineru"
    if venv_cli.exists():
        return [str(venv_cli)]
    sys_cli = shutil.which("mineru")
    if sys_cli:
        return [sys_cli]
    if importlib.util.find_spec("mineru"):
        return [sys.executable, "-m", "mineru"]
    return []


def pdf_to_markdown_with_pypdf(pdf_path: Path, md_path: Path) -> tuple[str, str]:
    joined = ""
    pypdf_error = ""

    try:
        try:
            from pypdf import PdfReader
        except Exception:
            from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(str(pdf_path))
        text_parts = []
        for page in reader.pages:
            txt = (page.extract_text() or "").strip()
            if txt:
                text_parts.append(re.sub(r"\s+\n", "\n", txt))
        joined = "\n\n".join(text_parts).strip()
        if joined:
            status = "success_pypdf"
        else:
            status = "pypdf_no_text_extracted"
    except Exception as e:
        status = ""
        pypdf_error = f"pypdf_error:{str(e)[:120]}"

    # Fallback parser for malformed PDFs (PyMuPDF)
    if not joined:
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(pdf_path))
            text_parts = []
            for page in doc:
                txt = (page.get_text("text") or "").strip()
                if txt:
                    text_parts.append(txt)
            doc.close()
            joined = "\n\n".join(text_parts).strip()
            if joined:
                status = "success_fitz"
        except Exception as e:
            if pypdf_error:
                status = f"{pypdf_error}|fitz_error:{str(e)[:120]}"
            else:
                status = f"fitz_error:{str(e)[:120]}"

    if not joined:
        if not status:
            status = "pdf_no_text_extracted"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# {pdf_path.stem}",
            "",
            f"- Source PDF: `{pdf_path}`",
            "",
            "## Extracted Text",
            "",
            "(No extractable text from local parser. Use MinerU OCR pipeline for this file.)",
            "",
        ]
        md_path.write_text("\n".join(lines), encoding="utf-8")
        return str(md_path), f"placeholder_no_text:{status}"

    md_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {pdf_path.stem}", "", f"- Source PDF: `{pdf_path}`", "", "## Extracted Text", "", joined, ""]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return str(md_path), status


def pdf_to_markdown_with_mineru(
    pdf_path: Path,
    out_root: Path,
    backend: str = "pipeline",
    timeout_sec: int = 900,
) -> tuple[str, str]:
    cmd_head = _detect_mineru_cmd()
    if not cmd_head:
        return pdf_to_markdown_with_pypdf(pdf_path, out_root / f"{pdf_path.stem}.md")

    out_dir = out_root / pdf_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [*cmd_head, "-p", str(pdf_path), "-o", str(out_dir), "-b", backend]
    try:
        subprocess.run(cmd, check=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        return "", "mineru_timeout"
    except subprocess.CalledProcessError as e:
        return "", f"mineru_failed:{str(e)[:120]}"
    except Exception as e:
        return "", f"mineru_error:{str(e)[:120]}"

    md_files = sorted(
        out_dir.rglob("*.md"),
        key=lambda p: p.stat().st_size if p.exists() else 0,
        reverse=True,
    )
    if not md_files:
        return "", "mineru_no_md_output"
    return str(md_files[0]), "success"


class PlaywrightFallbackDownloader:
    def __init__(self, headless: bool, timeout_ms: int):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        from playwright.sync_api import sync_playwright

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        self.context = self.browser.new_context(
            accept_downloads=True,
            user_agent=DEFAULT_USER_AGENT,
        )
        self.page = self.context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def _find_pdf_url(self) -> str:
        selectors = [
            "a[data-article-pdf]",
            "a.c-pdf-download__link",
            "a[data-panel='PDF']",
            "a.article-tool-pdf",
            "a[href*='/content/pdf/']",
            "a[href*='/doi/pdf/']",
            "a[href*='.pdf']",
            "a:has-text('Download PDF')",
            "a:has-text('Full Text (PDF)')",
            "a:has-text('PDF')",
        ]
        for sel in selectors:
            try:
                el = self.page.query_selector(sel)
                if not el:
                    continue
                href = el.get_attribute("href")
                if href:
                    return href
            except Exception:
                continue
        return ""

    def _derive_pdf_url(self, current_url: str) -> str:
        if "/doi/abs/" in current_url:
            return current_url.replace("/doi/abs/", "/doi/pdf/")
        if "/doi/full/" in current_url:
            return current_url.replace("/doi/full/", "/doi/pdf/")
        if "/article/" in current_url and "nature.com" in current_url:
            return current_url.replace("/article/", "/content/pdf/") + ".pdf"
        return ""

    def download(self, doi: str, out_pdf: Path) -> AttemptResult:
        try:
            self.page.goto(f"https://doi.org/{doi}", wait_until="domcontentloaded", timeout=self.timeout_ms)
            self.page.wait_for_timeout(2000)
            current_url = self.page.url

            href = self._find_pdf_url()
            if href:
                pdf_url = urljoin(current_url, href)
            else:
                pdf_url = self._derive_pdf_url(current_url)
            if not pdf_url:
                return AttemptResult(source="playwright", status="no_pdf_link_found", success=False, detail=current_url)

            try:
                with self.page.expect_download(timeout=self.timeout_ms) as dl_info:
                    self.page.goto(pdf_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                dl = dl_info.value
                dl.save_as(str(out_pdf))
            except Exception:
                resp = self.page.goto(pdf_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                if not resp:
                    return AttemptResult(source="playwright", status="no_response", success=False, detail=pdf_url)
                body = resp.body() or b""
                if not is_pdf_bytes(body):
                    ctype = (resp.headers.get("content-type") or "").lower()
                    return AttemptResult(
                        source="playwright",
                        status=f"not_pdf:{ctype or 'unknown'}",
                        success=False,
                        detail=pdf_url,
                        http_status=resp.status,
                    )
                out_pdf.write_bytes(body)

            body = out_pdf.read_bytes()
            if not is_pdf_bytes(body):
                if out_pdf.exists():
                    out_pdf.unlink()
                return AttemptResult(source="playwright", status="invalid_pdf", success=False, detail=pdf_url)

            return AttemptResult(
                source="playwright",
                status="success",
                success=True,
                pdf_path=str(out_pdf),
                download_path=str(out_pdf),
                download_type="pdf",
                bytes_size=len(body),
                detail=pdf_url,
            )
        except Exception as e:
            return AttemptResult(source="playwright", status=f"error:{str(e)[:120]}", success=False)


class FulltextChainWrapper:
    def __init__(
        self,
        elsevier_api_key: str,
        elsevier_inst_token: str,
        wiley_token: str,
        openalex_api_key: str,
        openalex_mailto: str,
        timeout: int,
        max_retries: int,
        backoff_seconds: float,
    ):
        self.elsevier_api_key = (elsevier_api_key or "").strip()
        self.elsevier_inst_token = (elsevier_inst_token or "").strip()
        self.wiley_token = (wiley_token or "").strip()
        self.openalex_api_key = (openalex_api_key or "").strip()
        self.openalex_mailto = (openalex_mailto or "").strip()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

    def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> requests.Response:
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        sleep_s = max(float(retry_after), self.backoff_seconds)
                    else:
                        sleep_s = self.backoff_seconds * (2**attempt)
                    time.sleep(sleep_s)
                    continue
                return resp
            except requests.RequestException as e:
                last_exc = e
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * (2**attempt))
                    continue
                raise
        if last_exc:
            raise last_exc
        raise RuntimeError("Unexpected retry state")

    def try_elsevier(self, doi: str, out_xml: Path) -> AttemptResult:
        if not self.elsevier_api_key:
            return AttemptResult(source="elsevier", status="missing_elsevier_api_key", success=False)
        if not is_elsevier_doi(doi):
            return AttemptResult(source="elsevier", status="not_elsevier_doi", success=False)

        headers = {"X-ELS-APIKey": self.elsevier_api_key, "Accept": "text/xml"}
        if self.elsevier_inst_token:
            headers["X-ELS-Insttoken"] = self.elsevier_inst_token

        url = f"{ELSEVIER_BASE_URL}/{quote(doi, safe='')}"
        params = {"view": "FULL", "httpAccept": "text/xml"}

        try:
            resp = self._request_with_retry("GET", url, headers=headers, params=params)
        except Exception as e:
            return AttemptResult(source="elsevier", status=f"error:{str(e)[:120]}", success=False)

        if resp.status_code >= 400:
            return AttemptResult(
                source="elsevier",
                status=f"http_{resp.status_code}",
                success=False,
                http_status=resp.status_code,
                detail=(resp.text or "").strip().replace("\n", " ")[:240],
            )

        body = resp.content or b""
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "xml" not in ctype and not is_xml_bytes(body):
            return AttemptResult(source="elsevier", status=f"not_xml:{ctype or 'unknown'}", success=False)

        out_xml.write_bytes(body)
        api_status = resp.headers.get("X-ELS-Status", "")
        limited = "limited to first page" in api_status.lower()

        return AttemptResult(
            source="elsevier",
            status="success_limited_xml" if limited else "success_xml",
            success=True,
            limited=limited,
            http_status=resp.status_code,
            api_status=api_status,
            download_path=str(out_xml),
            download_type="xml",
            bytes_size=len(body),
        )

    def try_wiley(self, doi: str, out_pdf: Path) -> AttemptResult:
        if not self.wiley_token:
            return AttemptResult(source="wiley", status="missing_wiley_token", success=False)
        if not is_wiley_doi(doi):
            return AttemptResult(source="wiley", status="not_wiley_doi", success=False)

        url = f"{WILEY_BASE_URL}/{doi}"
        headers = {"Wiley-TDM-Client-Token": self.wiley_token}
        try:
            resp = self._request_with_retry("GET", url, headers=headers)
        except Exception as e:
            return AttemptResult(source="wiley", status=f"error:{str(e)[:120]}", success=False)

        if resp.status_code >= 400:
            return AttemptResult(
                source="wiley",
                status=f"http_{resp.status_code}",
                success=False,
                http_status=resp.status_code,
                detail=(resp.text or "").strip().replace("\n", " ")[:240],
            )

        body = resp.content or b""
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if not is_pdf_bytes(body) and "pdf" not in ctype:
            return AttemptResult(source="wiley", status=f"not_pdf:{ctype or 'unknown'}", success=False)

        out_pdf.write_bytes(body)
        if not is_pdf_bytes(body):
            return AttemptResult(source="wiley", status="invalid_pdf", success=False)

        return AttemptResult(
            source="wiley",
            status="success",
            success=True,
            http_status=resp.status_code,
            pdf_path=str(out_pdf),
            download_path=str(out_pdf),
            download_type="pdf",
            bytes_size=len(body),
        )

    def _resolve_openalex_work(self, doi: str) -> tuple[str, dict]:
        if not self.openalex_api_key:
            return "", {}
        url = f"{OPENALEX_META_BASE_URL}/doi:{quote(doi, safe='')}"
        params = {"api_key": self.openalex_api_key}
        if self.openalex_mailto:
            params["mailto"] = self.openalex_mailto
        resp = self._request_with_retry("GET", url, params=params)
        if resp.status_code >= 400:
            return "", {"status": f"http_{resp.status_code}", "detail": (resp.text or "")[:240]}
        try:
            payload = resp.json()
        except json.JSONDecodeError:
            return "", {"status": "invalid_json"}
        work_id = (payload.get("id") or "").strip()
        work_id = re.sub(r"^https?://openalex\.org/", "", work_id, flags=re.IGNORECASE)
        return work_id, payload

    def try_openalex(self, doi: str, out_pdf: Path) -> AttemptResult:
        if not self.openalex_api_key:
            return AttemptResult(source="openalex", status="missing_openalex_api_key", success=False)

        try:
            work_id, payload = self._resolve_openalex_work(doi)
        except Exception as e:
            return AttemptResult(source="openalex", status=f"resolve_error:{str(e)[:120]}", success=False)

        if not work_id:
            return AttemptResult(
                source="openalex",
                status="doi_unresolved",
                success=False,
                detail=(payload or {}).get("status", ""),
            )

        open_access = payload.get("open_access", {}) or {}
        has_content = payload.get("has_content", {}) or {}
        has_pdf_flag = bool(has_content.get("pdf"))
        if not has_pdf_flag and not open_access.get("is_oa"):
            return AttemptResult(source="openalex", status="no_pdf_content_flag", success=False, detail=work_id)

        url = f"{OPENALEX_CONTENT_BASE_URL}/{quote(work_id, safe='')}.pdf"
        params = {"api_key": self.openalex_api_key}
        if self.openalex_mailto:
            params["mailto"] = self.openalex_mailto

        try:
            resp = self._request_with_retry("GET", url, params=params)
        except Exception as e:
            return AttemptResult(source="openalex", status=f"download_error:{str(e)[:120]}", success=False)

        if resp.status_code >= 400:
            return AttemptResult(
                source="openalex",
                status=f"http_{resp.status_code}",
                success=False,
                http_status=resp.status_code,
                detail=(resp.text or "").strip().replace("\n", " ")[:240],
            )

        body = resp.content or b""
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if not is_pdf_bytes(body) and "pdf" not in ctype:
            return AttemptResult(source="openalex", status=f"not_pdf:{ctype or 'unknown'}", success=False, detail=work_id)

        out_pdf.write_bytes(body)
        if not is_pdf_bytes(body):
            return AttemptResult(source="openalex", status="invalid_pdf", success=False, detail=work_id)

        return AttemptResult(
            source="openalex",
            status="success",
            success=True,
            pdf_path=str(out_pdf),
            download_path=str(out_pdf),
            download_type="pdf",
            bytes_size=len(body),
            detail=work_id,
            http_status=resp.status_code,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Full-text chain wrapper: OpenAlex(OA) -> Wiley/Elsevier(API) -> Playwright fallback"
    )
    parser.add_argument("--doi", action="append", default=[], help="DOI (repeat for multiple)")
    parser.add_argument("--doi-file", default="", help="DOI file (txt/csv/json/jsonl)")
    parser.add_argument("--doi-column", default="doi")
    parser.add_argument("--title-column", default="title")
    parser.add_argument("--journal-column", default="journal")
    parser.add_argument("--out-dir", default="fulltext_chain_outputs")

    parser.add_argument("--elsevier-api-key", default=os.getenv("ELSEVIER_API_KEY", ""))
    parser.add_argument("--elsevier-inst-token", default=os.getenv("ELSEVIER_INST_TOKEN", ""))
    parser.add_argument("--wiley-token", default=os.getenv("WILEY_TDM_CLIENT_TOKEN", ""))
    parser.add_argument("--openalex-api-key", default=os.getenv("OPENALEX_API_KEY", ""))
    parser.add_argument("--openalex-mailto", default=os.getenv("OPENALEX_MAILTO", ""))

    parser.add_argument("--use-playwright-fallback", action="store_true")
    parser.add_argument("--playwright-visible", action="store_true", help="Run Playwright in visible mode")
    parser.add_argument("--playwright-timeout-ms", type=int, default=60000)

    parser.add_argument(
        "--convert-to-md",
        action="store_true",
        help="Convert downloaded content to Markdown (XML: built-in; PDF: MinerU if available).",
    )
    parser.add_argument("--mineru-backend", default="pipeline", choices=["pipeline", "vlm"])
    parser.add_argument("--mineru-timeout-sec", type=int, default=900)

    parser.add_argument(
        "--accept-elsevier-limited-as-success",
        action="store_true",
        help="If Elsevier XML is limited, accept it immediately instead of trying downstream methods.",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--backoff-seconds", type=float, default=DEFAULT_BACKOFF_SECONDS)
    args = parser.parse_args()

    file_records = []
    if args.doi_file:
        p = Path(args.doi_file).resolve()
        if not p.exists():
            raise SystemExit(f"DOI file not found: {p}")
        file_records = load_records_from_file(
            p,
            doi_column=args.doi_column,
            title_column=args.title_column,
            journal_column=args.journal_column,
        )

    cli_records = [{"doi": x, "title": "", "journal": ""} for x in args.doi]
    records = unique_keep_order([*cli_records, *file_records])
    if not records:
        raise SystemExit("No DOI provided. Use --doi and/or --doi-file.")

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    downloads_root = out_dir / "downloads"
    md_root = out_dir / "md"
    for sub in ["elsevier", "wiley", "openalex", "playwright"]:
        (downloads_root / sub).mkdir(parents=True, exist_ok=True)
    if args.convert_to_md:
        for sub in ["elsevier", "wiley", "openalex", "playwright"]:
            (md_root / sub).mkdir(parents=True, exist_ok=True)

    wrapper = FulltextChainWrapper(
        elsevier_api_key=args.elsevier_api_key,
        elsevier_inst_token=args.elsevier_inst_token,
        wiley_token=args.wiley_token,
        openalex_api_key=args.openalex_api_key,
        openalex_mailto=args.openalex_mailto,
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
    )

    playwright_dl = None
    playwright_error = ""
    if args.use_playwright_fallback:
        try:
            playwright_dl = PlaywrightFallbackDownloader(
                headless=not args.playwright_visible,
                timeout_ms=args.playwright_timeout_ms,
            ).__enter__()
        except Exception as e:
            playwright_error = str(e)[:200]

    def attach_md(download_path: str, download_type: str, source: str) -> tuple[str, str]:
        if not args.convert_to_md:
            return "", "disabled"
        p = Path(download_path)
        if not p.exists():
            return "", "missing_download_file"
        if download_type == "xml":
            return xml_to_markdown(p, md_root / source / f"{p.stem}.md")
        if download_type == "pdf":
            return pdf_to_markdown_with_mineru(
                p,
                out_root=md_root / source,
                backend=args.mineru_backend,
                timeout_sec=args.mineru_timeout_sec,
            )
        return "", "unsupported_download_type"

    results = []
    try:
        for item in tqdm(records, desc="Fulltext chain"):
            doi = normalize_doi(item.get("doi", ""))
            title = (item.get("title") or "").strip()
            journal = (item.get("journal") or "").strip()

            row = {
                "doi": doi,
                "title": title,
                "journal": journal,
                "success": False,
                "final_source": "",
                "final_status": "",
                "download_path": "",
                "download_type": "",
                "pdf_path": "",
                "file_bytes": 0,
                "elsevier_status": "",
                "wiley_status": "",
                "openalex_status": "",
                "playwright_status": "",
                "md_path": "",
                "md_status": "",
                "note": "",
            }

            def mark_success(source: str, attempt: AttemptResult):
                row.update(
                    {
                        "success": True,
                        "final_source": source,
                        "final_status": attempt.status,
                        "download_path": attempt.download_path or attempt.pdf_path,
                        "download_type": attempt.download_type,
                        "file_bytes": attempt.bytes_size,
                    }
                )
                if attempt.download_type == "pdf":
                    row["pdf_path"] = attempt.download_path or attempt.pdf_path
                if attempt.api_status:
                    row["note"] = attempt.api_status
                elif attempt.detail:
                    row["note"] = attempt.detail
                md_path, md_status = attach_md(row["download_path"], row["download_type"], source)
                row["md_path"] = md_path
                row["md_status"] = md_status

            limited_elsevier_candidate = None

            # 1) OpenAlex OA / content API first
            r3 = wrapper.try_openalex(
                doi,
                downloads_root / "openalex" / safe_filename(title=title, doi=doi, suffix=".pdf"),
            )
            row["openalex_status"] = r3.status
            if r3.success:
                mark_success("openalex", r3)
                results.append(row)
                continue

            # 2) Publisher APIs
            # 2a) Wiley PDF
            if is_wiley_doi(doi):
                r2 = wrapper.try_wiley(
                    doi,
                    downloads_root / "wiley" / safe_filename(title=title, doi=doi, suffix=".pdf"),
                )
                row["wiley_status"] = r2.status
                if r2.success:
                    mark_success("wiley", r2)
                    results.append(row)
                    continue

            # 2b) Elsevier XML
            if is_elsevier_doi(doi):
                r1 = wrapper.try_elsevier(
                    doi,
                    downloads_root / "elsevier" / safe_filename(title=title, doi=doi, suffix=".xml"),
                )
                row["elsevier_status"] = r1.status
                if r1.success:
                    if r1.limited and not args.accept_elsevier_limited_as_success:
                        limited_elsevier_candidate = r1
                    else:
                        mark_success("elsevier", r1)
                        results.append(row)
                        continue

            # 3) Playwright fallback
            if args.use_playwright_fallback:
                if playwright_dl is None:
                    row["playwright_status"] = f"playwright_unavailable:{playwright_error or 'init_failed'}"
                else:
                    r4 = playwright_dl.download(
                        doi,
                        downloads_root / "playwright" / safe_filename(title=title, doi=doi, suffix=".pdf"),
                    )
                    row["playwright_status"] = r4.status
                    if r4.success:
                        mark_success("playwright", r4)
                        results.append(row)
                        continue

            if limited_elsevier_candidate is not None:
                mark_success("elsevier", limited_elsevier_candidate)
                row["note"] = "fallback_kept_limited_xml"
                results.append(row)
                continue

            row["final_status"] = "all_methods_failed"
            row["md_status"] = "not_applicable"
            results.append(row)
    finally:
        if playwright_dl is not None:
            try:
                playwright_dl.__exit__(None, None, None)
            except Exception:
                pass

    results_json = out_dir / "results.json"
    results_csv = out_dir / "results.csv"
    summary_json = out_dir / "run_summary.json"

    results_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    cols = [
        "doi",
        "title",
        "journal",
        "success",
        "final_source",
        "final_status",
        "download_path",
        "download_type",
        "pdf_path",
        "file_bytes",
        "elsevier_status",
        "wiley_status",
        "openalex_status",
        "playwright_status",
        "md_path",
        "md_status",
        "note",
    ]
    with results_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in results:
            w.writerow({c: r.get(c, "") for c in cols})

    summary = {
        "total": len(results),
        "success": sum(1 for x in results if x.get("success")),
        "failed": sum(1 for x in results if not x.get("success")),
        "by_source": {
            "elsevier": sum(1 for x in results if x.get("final_source") == "elsevier"),
            "wiley": sum(1 for x in results if x.get("final_source") == "wiley"),
            "openalex": sum(1 for x in results if x.get("final_source") == "openalex"),
            "playwright": sum(1 for x in results if x.get("final_source") == "playwright"),
        },
        "by_download_type": {
            "xml": sum(1 for x in results if x.get("download_type") == "xml"),
            "pdf": sum(1 for x in results if x.get("download_type") == "pdf"),
        },
        "md_generated": sum(1 for x in results if bool(x.get("md_path"))),
        "md_success_strict": sum(
            1 for x in results if x.get("md_status") in {"success", "success_pypdf", "success_fitz"}
        ),
        "playwright_enabled": bool(args.use_playwright_fallback),
        "convert_to_md": bool(args.convert_to_md),
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"Done. total={summary['total']} success={summary['success']} failed={summary['failed']} "
        f"elsevier={summary['by_source']['elsevier']} wiley={summary['by_source']['wiley']} "
        f"openalex={summary['by_source']['openalex']} playwright={summary['by_source']['playwright']} "
        f"xml={summary['by_download_type']['xml']} pdf={summary['by_download_type']['pdf']} "
        f"md_generated={summary['md_generated']} md_success={summary['md_success_strict']}"
    )
    print(f"Results CSV: {results_csv}")
    print(f"Results JSON: {results_json}")
    print(f"Summary: {summary_json}")
    print(f"Downloads root: {downloads_root}")
    if args.convert_to_md:
        print(f"Markdown root: {md_root}")


if __name__ == "__main__":
    main()
