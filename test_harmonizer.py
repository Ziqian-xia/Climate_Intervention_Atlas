"""Quick smoke test for the database harmonizer (no API required)."""

import pandas as pd
from utils.harmonizer import harmonize, harmonize_and_merge, get_harmonization_report, detect_database, CANONICAL_COLUMNS

# ── Sample data mimicking each database's works_summary.csv ──────────────────

OPENALEX_ROWS = [
    {"openalex_id": "W1", "doi": "https://doi.org/10.1000/xyz001", "title": "Heat wave and mortality A",
     "abstract": "Abstract A", "publication_year": 2021, "cited_by_count": 42, "is_oa": True},
    {"openalex_id": "W2", "doi": "10.1000/xyz002", "title": "Climate adaptation B",
     "abstract": "Abstract B", "publication_year": 2020, "cited_by_count": 10, "is_oa": False},
    {"openalex_id": "W3", "doi": "", "title": "No DOI paper C",
     "abstract": "Abstract C", "publication_year": 2019, "cited_by_count": 0, "is_oa": False},
]

PUBMED_ROWS = [
    {"pmid": "11111", "doi": "10.1000/xyz001",  # duplicate of OpenAlex W1
     "title": "Heat wave and mortality A (PubMed version)",
     "abstract": "Abstract A pubmed", "journal_title": "Nature Climate", "publication_date": "2021-06-15"},
    {"pmid": "22222", "doi": "10.1000/xyz003",
     "title": "Urban heat island D",
     "abstract": "Abstract D", "journal_title": "Lancet Planetary Health", "publication_date": "2022-01-01"},
    {"pmid": "33333", "doi": "",
     "title": "No DOI pubmed paper",
     "abstract": "Abstract E", "journal_title": "NEJM", "publication_date": "2021"},
]

SCOPUS_ROWS = [
    {"eid": "S-001", "doi": "10.1000/xyz002",  # duplicate of OpenAlex W2
     "title": "Climate adaptation B (Scopus)",
     "abstract": "Abstract B scopus", "creator": "Smith J.",
     "publication_name": "Global Env Change", "cover_date": "2020-03-01", "citedby_count": "15"},
    {"eid": "S-002", "doi": "10.1000/xyz004",
     "title": "Green infrastructure E",
     "abstract": "Abstract F", "creator": "Jones K.",
     "publication_name": "Urban Climate", "cover_date": "2023-07-01", "citedby_count": "3"},
]

# ─────────────────────────────────────────────────────────────────────────────

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def test_detect_database():
    section("1 · detect_database()")
    df_oa  = pd.DataFrame(OPENALEX_ROWS)
    df_pm  = pd.DataFrame(PUBMED_ROWS)
    df_sc  = pd.DataFrame(SCOPUS_ROWS)

    assert detect_database(df_oa) == "openalex", "OpenAlex detection failed"
    assert detect_database(df_pm) == "pubmed",   "PubMed detection failed"
    assert detect_database(df_sc) == "scopus",   "Scopus detection failed"
    print("✅  All databases correctly detected")


def test_harmonize_single():
    section("2 · harmonize() – per database")
    for db, rows in [("openalex", OPENALEX_ROWS), ("pubmed", PUBMED_ROWS), ("scopus", SCOPUS_ROWS)]:
        raw = pd.DataFrame(rows)
        h   = harmonize(raw, source_db=db)

        # Schema check
        assert list(h.columns) == CANONICAL_COLUMNS, f"{db}: wrong columns {list(h.columns)}"
        # source_db column
        assert (h["source_db"] == db).all(), f"{db}: wrong source_db values"
        # DOI cleaned (no URL prefix)
        assert not h["doi"].str.startswith("http").any(), f"{db}: DOI still has URL prefix"

        print(f"\n  [{db}]  {len(h)} rows")
        print(h[["doi","title","journal","year","citations","source_db"]].to_string(index=False))

    print("\n✅  Single-DB harmonization passed")


def test_harmonize_and_merge():
    section("3 · harmonize_and_merge() – deduplication")
    dbs = {
        "openalex": pd.DataFrame(OPENALEX_ROWS),
        "pubmed":   pd.DataFrame(PUBMED_ROWS),
        "scopus":   pd.DataFrame(SCOPUS_ROWS),
    }

    merged = harmonize_and_merge(dbs)

    total_raw   = sum(len(pd.DataFrame(r)) for r in [OPENALEX_ROWS, PUBMED_ROWS, SCOPUS_ROWS])
    duplicates  = 2  # xyz001 (OA+PM) and xyz002 (OA+SC)
    expected    = total_raw - duplicates

    print(f"\n  Raw total   : {total_raw}")
    print(f"  After dedup : {len(merged)}  (expected {expected})")
    print(f"  Removed     : {total_raw - len(merged)} duplicates")
    assert len(merged) == expected, f"Expected {expected} rows, got {len(merged)}"

    # Duplicate DOIs kept from first-seen DB (openalex)
    row_xyz001 = merged[merged["doi"] == "10.1000/xyz001"].iloc[0]
    assert row_xyz001["source_db"] == "openalex", "xyz001 should be kept from openalex"

    print("\n  Merged result:")
    print(merged[["doi","title","journal","year","citations","source_db"]].to_string(index=False))
    print("\n✅  Merge and deduplication passed")


def test_harmonization_report():
    section("4 · get_harmonization_report()")
    dbs_raw = {
        "openalex": pd.DataFrame(OPENALEX_ROWS),
        "pubmed":   pd.DataFrame(PUBMED_ROWS),
        "scopus":   pd.DataFrame(SCOPUS_ROWS),
    }
    merged = harmonize_and_merge(dbs_raw)
    report = get_harmonization_report(dbs_raw, merged)

    print(f"\n  Total before dedup : {report['total_before_dedup']}")
    print(f"  Total after dedup  : {report['total_after_dedup']}")
    print(f"  Duplicates removed : {report['duplicates_removed']}")
    for db, stats in report["per_database"].items():
        print(f"  {db:10s}  raw={stats['raw']}  in_merged={stats['in_merged']}")

    assert report["duplicates_removed"] == 2
    print("\n✅  Report generation passed")


def test_year_extraction():
    section("5 · Year extraction edge cases")
    import pandas as pd
    from utils.harmonizer import _extract_year

    cases = [
        ("2022-03-15", 2022),
        ("2022",       2022),
        ("Jan 2019",   2019),
        ("",           None),
        (None,         None),
        ("no year",    None),
    ]
    for val, expected in cases:
        got = _extract_year(val)
        status = "✅" if got == expected else "❌"
        print(f"  {status}  _extract_year({val!r:15}) → {got}  (expected {expected})")
        assert got == expected, f"Failed for {val!r}"

    print("\n✅  Year extraction passed")


if __name__ == "__main__":
    print("\n🔬  Harmonizer Quick Test  (no API required)\n")
    test_detect_database()
    test_harmonize_single()
    test_harmonize_and_merge()
    test_harmonization_report()
    test_year_extraction()
    print("\n" + "="*60)
    print("  ✅  All tests passed!")
    print("="*60 + "\n")
