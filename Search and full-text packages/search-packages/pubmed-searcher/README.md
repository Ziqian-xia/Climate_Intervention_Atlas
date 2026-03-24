# PubMed Searcher

Standalone PubMed metadata search package based on NCBI E-utilities.

## Purpose

`pubmed_search_wrapper.py` executes PubMed/Entrez queries, retrieves PMID sets with `ESearch`, fetches records with `EFetch`, and exports title/abstract-focused metadata.

## Install

```bash
cd /Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/search-packages/pubmed-searcher
python3 -m pip install -r requirements.txt
```

## Authentication

Optional but recommended:

```bash
export PUBMED_API_KEY="YOUR_NCBI_API_KEY"
export PUBMED_EMAIL="your_email@domain.com"
```

Without key, NCBI limit is lower. With key, throughput ceiling is higher.

## Query Syntax

Use PubMed/Entrez syntax, for example:
- `("heat"[Title/Abstract] AND mortality[Title/Abstract])`
- `("tropical cyclone"[Title/Abstract] AND "mental health"[Title/Abstract])`
- `("Heat Stress Disorders"[MeSH Terms] AND mortality[Title/Abstract])`

## Basic Run

```bash
python3 pubmed_search_wrapper.py \
  --query-file sample_queries.txt \
  --max-results-per-query 1000 \
  --fetch-batch-size 200 \
  --out-dir run_pubmed
```

## Key CLI Options

- `--query` (repeatable) and/or `--query-file` (`txt/csv/json/jsonl`)
- `--sort`, `--datetype`, `--mindate`, `--maxdate`
- `--fetch-batch-size` (default 200)
- `--include-raw-xml` for debugging/audit
- `--keep-duplicates` to keep duplicated PMIDs across queries

## Outputs

- `run_summary.json`
- `works_summary.csv`
- `works_full.jsonl`
- `query_runs/*.json`

Primary CSV columns:
- `pmid`, `doi`, `pmcid`, `title`, `abstract`, `journal_title`, `publication_date`

## Notes

- Wrapper uses `usehistory=y` in `ESearch`, then batch fetches via `query_key + WebEnv`.
- Empty abstract is normal for some PMIDs.
- Set explicit `--max-results-per-query` for broad queries.

## Docs

- E-utilities overview: <https://www.ncbi.nlm.nih.gov/books/NBK25501/>
- ESearch and EFetch reference: <https://www.ncbi.nlm.nih.gov/books/NBK25499/>
