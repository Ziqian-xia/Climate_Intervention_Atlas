#!/usr/bin/env python3
"""
PubMed search wrapper (workflow search step):
- Input PubMed/Entrez query strings
- Retrieve many PubMed records via E-utilities
- Export structured metadata with focus on title + abstract

APIs:
- ESearch: find PMIDs for a query
- EFetch: fetch detailed PubMed XML by history server query_key/WebEnv
"""

import argparse
import csv
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Optional

import requests
from tqdm import tqdm


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
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


def text_from_node(node: Optional[ET.Element]) -> str:
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


def parse_pubdate(article: ET.Element) -> str:
    # Prefer ArticleDate if present.
    ad = article.find("./ArticleDate")
    if ad is not None:
        y = (ad.findtext("Year") or "").strip()
        m = (ad.findtext("Month") or "").strip()
        d = (ad.findtext("Day") or "").strip()
        if y:
            return "-".join([x for x in [y, m, d] if x])

    pub = article.find("./Journal/JournalIssue/PubDate")
    if pub is None:
        return ""
    y = (pub.findtext("Year") or "").strip()
    m = (pub.findtext("Month") or "").strip()
    d = (pub.findtext("Day") or "").strip()
    medline = (pub.findtext("MedlineDate") or "").strip()
    if y:
        return "-".join([x for x in [y, m, d] if x])
    return medline


def parse_pubmed_xml(xml_text: str, include_raw_xml: bool = False) -> list[dict]:
    root = ET.fromstring(xml_text)
    out = []
    for pa in root.findall("./PubmedArticle"):
        mc = pa.find("./MedlineCitation")
        pd = pa.find("./PubmedData")
        if mc is None:
            continue

        pmid = (mc.findtext("./PMID") or "").strip()
        article = mc.find("./Article")
        if article is None:
            continue

        title = text_from_node(article.find("./ArticleTitle"))

        # Abstract can be structured with multiple AbstractText sections.
        abstract_parts = []
        for ab in article.findall("./Abstract/AbstractText"):
            label = (ab.attrib.get("Label") or ab.attrib.get("NlmCategory") or "").strip()
            content = text_from_node(ab)
            if not content:
                continue
            if label:
                abstract_parts.append(f"{label}: {content}")
            else:
                abstract_parts.append(content)
        abstract = "\n".join(abstract_parts).strip()

        journal_title = (article.findtext("./Journal/Title") or "").strip()
        journal_iso = (article.findtext("./Journal/ISOAbbreviation") or "").strip()
        pub_date = parse_pubdate(article)

        authors = []
        affiliations = []
        for au in article.findall("./AuthorList/Author"):
            collective = (au.findtext("./CollectiveName") or "").strip()
            if collective:
                authors.append(collective)
            else:
                last = (au.findtext("./LastName") or "").strip()
                fore = (au.findtext("./ForeName") or "").strip()
                initials = (au.findtext("./Initials") or "").strip()
                name = " ".join([x for x in [fore, last] if x]).strip()
                if not name:
                    name = initials
                if name:
                    authors.append(name)
            for aff in au.findall("./AffiliationInfo/Affiliation"):
                a = text_from_node(aff)
                if a:
                    affiliations.append(a)

        # IDs (doi, pmcid, etc.)
        doi = ""
        pmcid = ""
        pii = ""
        article_ids = []
        if pd is not None:
            for aid in pd.findall("./ArticleIdList/ArticleId"):
                id_type = (aid.attrib.get("IdType") or "").strip().lower()
                val = text_from_node(aid)
                if not val:
                    continue
                article_ids.append({"id_type": id_type, "value": val})
                if id_type == "doi" and not doi:
                    doi = val.lower()
                if id_type == "pmc" and not pmcid:
                    pmcid = val
                if id_type == "pii" and not pii:
                    pii = val

        keywords = []
        for kw in mc.findall("./KeywordList/Keyword"):
            k = text_from_node(kw)
            if k:
                keywords.append(k)

        mesh_terms = []
        for mh in mc.findall("./MeshHeadingList/MeshHeading"):
            desc_node = mh.find("./DescriptorName")
            desc = text_from_node(desc_node)
            qual_nodes = mh.findall("./QualifierName")
            quals = [text_from_node(x) for x in qual_nodes if text_from_node(x)]
            if desc:
                mesh_terms.append({"descriptor": desc, "qualifiers": quals})

        publication_types = []
        for pt in article.findall("./PublicationTypeList/PublicationType"):
            x = text_from_node(pt)
            if x:
                publication_types.append(x)

        languages = []
        for ln in article.findall("./Language"):
            x = text_from_node(ln)
            if x:
                languages.append(x)

        rec = {
            "pmid": pmid,
            "doi": doi,
            "pmcid": pmcid,
            "pii": pii,
            "title": title,
            "abstract": abstract,
            "journal_title": journal_title,
            "journal_iso": journal_iso,
            "publication_date": pub_date,
            "authors": authors,
            "affiliations": unique_keep_order(affiliations),
            "keywords": keywords,
            "mesh_terms": mesh_terms,
            "publication_types": publication_types,
            "languages": languages,
            "article_ids": article_ids,
        }
        if include_raw_xml:
            rec["raw_xml"] = ET.tostring(pa, encoding="unicode")
        out.append(rec)
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


class PubMedSearchWrapper:
    def __init__(
        self,
        api_key: str = "",
        email: str = "",
        tool: str = "climate_evidence_pubmed_wrapper",
        requests_per_second: float = 0.0,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    ):
        self.api_key = (api_key or "").strip()
        self.email = (email or "").strip()
        self.tool = (tool or "pubmed_wrapper").strip()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = requests.Session()

        if requests_per_second and requests_per_second > 0:
            self.rps = requests_per_second
        else:
            # NCBI guidance: 3 req/s without key, up to 10 req/s with key.
            self.rps = 9.0 if self.api_key else 2.8
        self.min_interval = 1.0 / self.rps
        self._last_request_ts = 0.0

    def _throttle(self):
        now = time.time()
        wait = self.min_interval - (now - self._last_request_ts)
        if wait > 0:
            time.sleep(wait)

    def _base_params(self) -> dict:
        p = {"tool": self.tool}
        if self.email:
            p["email"] = self.email
        if self.api_key:
            p["api_key"] = self.api_key
        return p

    def _request_with_retry(self, endpoint: str, params: dict) -> requests.Response:
        url = f"{EUTILS_BASE}/{endpoint}"
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                self._throttle()
                resp = self.session.get(url, params=params, timeout=self.timeout)
                self._last_request_ts = time.time()

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

    def esearch(
        self,
        query: str,
        max_results: int,
        sort: str = "",
        datetype: str = "",
        mindate: str = "",
        maxdate: str = "",
    ) -> dict:
        params = {
            **self._base_params(),
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "usehistory": "y",
            "retmax": 0,
        }
        if sort:
            params["sort"] = sort
        if datetype:
            params["datetype"] = datetype
        if mindate:
            params["mindate"] = mindate
        if maxdate:
            params["maxdate"] = maxdate

        resp = self._request_with_retry("esearch.fcgi", params=params)
        if resp.status_code >= 400:
            return {
                "ok": False,
                "status": f"http_{resp.status_code}",
                "error": (resp.text or "").strip().replace("\n", " ")[:240],
            }
        try:
            payload = resp.json()
        except json.JSONDecodeError:
            return {"ok": False, "status": "invalid_json", "error": "esearch non-json response"}

        er = payload.get("esearchresult", {}) or {}
        count = int(er.get("count", "0") or 0)
        qk = er.get("querykey", "")
        webenv = er.get("webenv", "")
        return {
            "ok": True,
            "status": "success",
            "count_total": count,
            "count_target": min(count, max_results),
            "query_key": qk,
            "webenv": webenv,
            "payload": payload,
        }

    def efetch_batch(self, query_key: str, webenv: str, retstart: int, retmax: int) -> dict:
        params = {
            **self._base_params(),
            "db": "pubmed",
            "query_key": query_key,
            "WebEnv": webenv,
            "retstart": retstart,
            "retmax": retmax,
            "retmode": "xml",
        }
        resp = self._request_with_retry("efetch.fcgi", params=params)
        if resp.status_code >= 400:
            return {
                "ok": False,
                "status": f"http_{resp.status_code}",
                "error": (resp.text or "").strip().replace("\n", " ")[:240],
                "xml": "",
            }
        return {"ok": True, "status": "success", "xml": resp.text}


def main():
    parser = argparse.ArgumentParser(description="PubMed query wrapper via NCBI E-utilities")
    parser.add_argument("--api-key", default=os.getenv("PUBMED_API_KEY", ""), help="NCBI E-utilities API key")
    parser.add_argument("--email", default=os.getenv("PUBMED_EMAIL", ""), help="Contact email for E-utilities")
    parser.add_argument("--tool", default="climate_evidence_pubmed_wrapper", help="NCBI tool identifier")
    parser.add_argument("--query", action="append", default=[], help="PubMed query string (repeat allowed)")
    parser.add_argument("--query-file", default="", help="Query file: txt/csv/json/jsonl")
    parser.add_argument("--query-column", default="query", help="Query column for CSV/JSON-object inputs")
    parser.add_argument("--sort", default="", help="ESearch sort, e.g. relevance, pub_date")
    parser.add_argument("--datetype", default="", help="ESearch date type: pdat, edat, mdat")
    parser.add_argument("--mindate", default="", help="Min date, e.g. 2015/01/01 or 2015")
    parser.add_argument("--maxdate", default="", help="Max date, e.g. 2026/12/31 or 2026")
    parser.add_argument("--max-results-per-query", type=int, default=1000)
    parser.add_argument("--fetch-batch-size", type=int, default=200, help="EFetch batch size")
    parser.add_argument("--include-raw-xml", action="store_true")
    parser.add_argument("--keep-duplicates", action="store_true", help="Keep duplicate PMIDs across queries")
    parser.add_argument("--requests-per-second", type=float, default=0.0, help="Override request rate")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--backoff-seconds", type=float, default=DEFAULT_BACKOFF_SECONDS)
    parser.add_argument("--out-dir", default="pubmed_search_outputs")
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

    wrapper = PubMedSearchWrapper(
        api_key=args.api_key,
        email=args.email,
        tool=args.tool,
        requests_per_second=args.requests_per_second,
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff_seconds=args.backoff_seconds,
    )

    run_summary = []
    summary_rows = []
    seen_pmids = set()
    total_stored = 0
    total_api_calls_est = 0

    full_jsonl_path = out_dir / "works_full.jsonl"
    summary_csv_path = out_dir / "works_summary.csv"
    run_summary_path = out_dir / "run_summary.json"

    with full_jsonl_path.open("w", encoding="utf-8") as jf:
        for idx, query in enumerate(tqdm(queries, desc="PubMed queries"), start=1):
            qrow = {
                "query_index": idx,
                "query": query,
                "status": "",
                "success": False,
                "count_total": 0,
                "count_target": 0,
                "stored_results": 0,
                "api_calls": 0,
                "raw_query_path": "",
                "error": "",
            }

            es = wrapper.esearch(
                query=query,
                max_results=args.max_results_per_query,
                sort=args.sort,
                datetype=args.datetype,
                mindate=args.mindate,
                maxdate=args.maxdate,
            )
            qrow["api_calls"] += 1
            if not es.get("ok"):
                qrow["status"] = es.get("status", "error")
                qrow["error"] = es.get("error", "")
                qrow["success"] = False
                run_summary.append(qrow)
                continue

            total = int(es.get("count_total", 0))
            target = int(es.get("count_target", 0))
            qrow["count_total"] = total
            qrow["count_target"] = target

            raw_query = {
                "query_index": idx,
                "query": query,
                "esearch": es.get("payload", {}),
                "fetched_batches": [],
            }

            fetched = 0
            batch_size = max(1, min(10000, args.fetch_batch_size))
            while fetched < target:
                n = min(batch_size, target - fetched)
                ef = wrapper.efetch_batch(
                    query_key=es.get("query_key", ""),
                    webenv=es.get("webenv", ""),
                    retstart=fetched,
                    retmax=n,
                )
                qrow["api_calls"] += 1
                if not ef.get("ok"):
                    qrow["status"] = ef.get("status", "error")
                    qrow["error"] = ef.get("error", "")
                    break

                try:
                    recs = parse_pubmed_xml(ef.get("xml", ""), include_raw_xml=args.include_raw_xml)
                except Exception as e:
                    qrow["status"] = "xml_parse_error"
                    qrow["error"] = str(e)[:200]
                    break

                raw_query["fetched_batches"].append(
                    {
                        "retstart": fetched,
                        "retmax": n,
                        "records_parsed": len(recs),
                    }
                )

                for rec in recs:
                    pmid = rec.get("pmid", "")
                    if not args.keep_duplicates and pmid and pmid in seen_pmids:
                        continue
                    if pmid:
                        seen_pmids.add(pmid)

                    row = {
                        "query_index": idx,
                        "query": query,
                        "pmid": rec.get("pmid", ""),
                        "doi": rec.get("doi", ""),
                        "pmcid": rec.get("pmcid", ""),
                        "title": rec.get("title", ""),
                        "abstract": rec.get("abstract", ""),
                        "journal_title": rec.get("journal_title", ""),
                        "journal_iso": rec.get("journal_iso", ""),
                        "publication_date": rec.get("publication_date", ""),
                        "authors_count": len(rec.get("authors", [])),
                        "keywords_count": len(rec.get("keywords", [])),
                        "mesh_terms_count": len(rec.get("mesh_terms", [])),
                    }
                    summary_rows.append(row)

                    full_payload = {
                        "query_index": idx,
                        "query": query,
                        "record": rec,
                    }
                    jf.write(json.dumps(full_payload, ensure_ascii=False) + "\n")
                    qrow["stored_results"] += 1
                    total_stored += 1

                fetched += n

            if not qrow["status"]:
                qrow["status"] = "success"
            qrow["success"] = qrow["status"] == "success"

            slug = f"{idx:03d}_{slugify(query)}.json"
            qpath = query_runs_dir / slug
            qpath.write_text(json.dumps(raw_query, ensure_ascii=False, indent=2), encoding="utf-8")
            qrow["raw_query_path"] = str(qpath)

            total_api_calls_est += qrow["api_calls"]
            run_summary.append(qrow)

    cols = [
        "query_index",
        "query",
        "pmid",
        "doi",
        "pmcid",
        "title",
        "abstract",
        "journal_title",
        "journal_iso",
        "publication_date",
        "authors_count",
        "keywords_count",
        "mesh_terms_count",
    ]
    with summary_csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in summary_rows:
            w.writerow({c: row.get(c, "") for c in cols})

    run_summary_path.write_text(json.dumps(run_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    success_queries = sum(1 for x in run_summary if x.get("success"))
    print(
        f"Done. queries={len(queries)}, success_queries={success_queries}, failed_queries={len(queries)-success_queries}"
    )
    print(f"Stored records: {total_stored}")
    print(f"Approx API calls: {total_api_calls_est}")
    print(f"Run summary: {run_summary_path}")
    print(f"Works summary CSV: {summary_csv_path}")
    print(f"Full metadata JSONL: {full_jsonl_path}")
    print(f"Per-query logs: {query_runs_dir}")


if __name__ == "__main__":
    main()
