"""
Database Result Harmonizer
Standardizes field names and formats across OpenAlex, PubMed, and Scopus.

Canonical schema:
  doi              - DOI string (lowercased, stripped)
  title            - Paper title
  abstract         - Abstract text
  authors          - Author string (first author or comma-separated list)
  journal          - Journal / venue name
  year             - Publication year (int)
  citations        - Citation count (int)
  is_oa            - Open access flag (bool)
  source_db        - Origin database: "openalex" | "pubmed" | "scopus"
  source_id        - Original database ID (openalex_id / pmid / eid)
"""

import re
from typing import Optional
import pandas as pd


# ─────────────────────────────────────────────
# Per-database field maps
# ─────────────────────────────────────────────

_OPENALEX_MAP = {
    "doi":           "doi",
    "title":         "title",
    "abstract":      "abstract",
    "publication_year": "year",
    "cited_by_count": "citations",
    "is_oa":         "is_oa",
    "openalex_id":   "source_id",
}

_PUBMED_MAP = {
    "doi":           "doi",
    "title":         "title",
    "abstract":      "abstract",
    "journal_title": "journal",
    "publication_date": "_pub_date",   # needs year extraction
    "pmid":          "source_id",
}

_SCOPUS_MAP = {
    "doi":           "doi",
    "title":         "title",
    "abstract":      "abstract",
    "creator":       "authors",
    "publication_name": "journal",
    "cover_date":    "_cover_date",    # needs year extraction
    "citedby_count": "citations",
    "eid":           "source_id",
}

CANONICAL_COLUMNS = [
    "doi", "title", "abstract", "authors",
    "journal", "year", "citations", "is_oa",
    "source_db", "source_id",
]


# ─────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────

def _extract_year(value) -> Optional[int]:
    """Extract 4-digit year from a string like '2022-03-15' or '2022'."""
    if pd.isna(value) or value == "":
        return None
    match = re.search(r"\b(19|20)\d{2}\b", str(value))
    return int(match.group()) if match else None


def _clean_doi(doi) -> str:
    if pd.isna(doi) or not str(doi).strip():
        return ""
    doi = str(doi).strip().lower()
    # Remove URL prefix if present
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi


# ─────────────────────────────────────────────
# Per-database harmonize functions
# ─────────────────────────────────────────────

def _harmonize_openalex(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["doi"]       = df.get("doi", pd.Series(dtype=str)).apply(_clean_doi)
    out["title"]     = df.get("title", pd.Series(dtype=str)).fillna("")
    out["abstract"]  = df.get("abstract", pd.Series(dtype=str)).fillna("")
    out["authors"]   = ""          # OpenAlex works_summary doesn't include authors
    out["journal"]   = ""          # Not included in works_summary CSV
    out["year"]      = pd.to_numeric(df.get("publication_year"), errors="coerce").astype("Int64")
    out["citations"] = pd.to_numeric(df.get("cited_by_count", 0), errors="coerce").fillna(0).astype(int)
    out["is_oa"]     = df.get("is_oa", False).fillna(False).astype(bool)
    out["source_db"] = "openalex"
    out["source_id"] = df.get("openalex_id", pd.Series(dtype=str)).fillna("")
    return out


def _harmonize_pubmed(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["doi"]       = df.get("doi", pd.Series(dtype=str)).apply(_clean_doi)
    out["title"]     = df.get("title", pd.Series(dtype=str)).fillna("")
    out["abstract"]  = df.get("abstract", pd.Series(dtype=str)).fillna("")
    out["authors"]   = ""          # Not included in works_summary CSV
    out["journal"]   = df.get("journal_title", pd.Series(dtype=str)).fillna("")
    out["year"]      = df.get("publication_date", pd.Series(dtype=str)).apply(_extract_year).astype("Int64")
    out["citations"] = 0
    out["is_oa"]     = False
    out["source_db"] = "pubmed"
    out["source_id"] = df.get("pmid", pd.Series(dtype=str)).fillna("").astype(str)
    return out


def _harmonize_scopus(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["doi"]       = df.get("doi", pd.Series(dtype=str)).apply(_clean_doi)
    out["title"]     = df.get("title", pd.Series(dtype=str)).fillna("")
    out["abstract"]  = df.get("abstract", pd.Series(dtype=str)).fillna("")
    out["authors"]   = df.get("creator", pd.Series(dtype=str)).fillna("")
    out["journal"]   = df.get("publication_name", pd.Series(dtype=str)).fillna("")
    out["year"]      = df.get("cover_date", pd.Series(dtype=str)).apply(_extract_year).astype("Int64")
    out["citations"] = pd.to_numeric(df.get("citedby_count", 0), errors="coerce").fillna(0).astype(int)
    out["is_oa"]     = False
    out["source_db"] = "scopus"
    out["source_id"] = df.get("eid", pd.Series(dtype=str)).fillna("")
    return out


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

_DB_HANDLERS = {
    "openalex": _harmonize_openalex,
    "pubmed":   _harmonize_pubmed,
    "scopus":   _harmonize_scopus,
}


def detect_database(df: pd.DataFrame) -> str:
    """Guess which database produced this DataFrame by checking unique columns."""
    cols = set(df.columns)
    if "openalex_id" in cols:
        return "openalex"
    if "pmid" in cols:
        return "pubmed"
    if "eid" in cols or "prism:doi" in cols:
        return "scopus"
    # Fallback: look for distinctive column names
    if "publication_year" in cols and "cited_by_count" in cols:
        return "openalex"
    if "journal_title" in cols and "publication_date" in cols:
        return "pubmed"
    if "publication_name" in cols or "cover_date" in cols:
        return "scopus"
    return "unknown"


def harmonize(df: pd.DataFrame, source_db: Optional[str] = None) -> pd.DataFrame:
    """
    Harmonize a single-database DataFrame to the canonical schema.

    Args:
        df: Raw works_summary DataFrame from one database.
        source_db: "openalex", "pubmed", or "scopus".
                   Auto-detected if not provided.

    Returns:
        DataFrame with CANONICAL_COLUMNS columns.
    """
    if source_db is None:
        source_db = detect_database(df)

    handler = _DB_HANDLERS.get(source_db)
    if handler is None:
        # Unknown DB: pass through with missing canonical fields filled with ""
        out = df.copy()
        for col in CANONICAL_COLUMNS:
            if col not in out.columns:
                out[col] = ""
        out["source_db"] = source_db
        return out[CANONICAL_COLUMNS]

    return handler(df)[CANONICAL_COLUMNS]


def harmonize_and_merge(db_dataframes: dict) -> pd.DataFrame:
    """
    Harmonize and merge results from multiple databases.

    Args:
        db_dataframes: dict mapping db name → raw DataFrame
                       e.g. {"openalex": df1, "pubmed": df2, "scopus": df3}

    Returns:
        Merged, deduplicated DataFrame with canonical columns.
        Deduplication priority: openalex > pubmed > scopus (by DOI, case-insensitive).
    """
    harmonized = []
    for db_name, df in db_dataframes.items():
        if df is None or df.empty:
            continue
        harmonized.append(harmonize(df, source_db=db_name))

    if not harmonized:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    combined = pd.concat(harmonized, ignore_index=True)

    # Deduplicate by DOI (keep first occurrence, priority order from concat)
    has_doi = combined["doi"].str.strip() != ""
    with_doi    = combined[has_doi].drop_duplicates(subset="doi", keep="first")
    without_doi = combined[~has_doi]
    result = pd.concat([with_doi, without_doi], ignore_index=True)

    return result.reset_index(drop=True)


def get_harmonization_report(original_dfs: dict, harmonized_df: pd.DataFrame) -> dict:
    """
    Generate a summary report of the harmonization process.

    Returns:
        Dict with per-database counts and deduplication stats.
    """
    total_before = sum(len(df) for df in original_dfs.values() if df is not None)
    total_after  = len(harmonized_df)

    per_db = {}
    for db, df in original_dfs.items():
        if df is None:
            per_db[db] = {"raw": 0, "in_merged": 0}
            continue
        count_in_merged = len(harmonized_df[harmonized_df["source_db"] == db])
        per_db[db] = {
            "raw": len(df),
            "in_merged": count_in_merged,
        }

    return {
        "total_before_dedup": total_before,
        "total_after_dedup":  total_after,
        "duplicates_removed": total_before - total_after,
        "per_database": per_db,
    }
