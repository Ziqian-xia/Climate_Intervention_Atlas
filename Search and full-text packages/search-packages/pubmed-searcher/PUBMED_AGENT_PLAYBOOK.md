# PubMed Agent Playbook

Last updated: 2026-03-22  
Scope: How agents should run PubMed retrieval in this repository.

## 1) Workflow Position

This wrapper is for the retrieval stage using PubMed queries:
1. Upstream generates query strings.
2. Agent runs `pubmed_search_wrapper.py`.
3. Agent exports title/abstract-focused table + structured full metadata.

## 2) API Stack

Use NCBI E-utilities:
- `esearch.fcgi` to discover PMIDs
- `efetch.fcgi` to fetch full PubMed XML metadata

Implementation in this repo:
- `pubmed_search_wrapper.py`

## 3) Authentication and Limits

Auth parameter:
- `api_key=...` (optional but recommended)

User-provided NCBI key management rule:
- No API key: 3 requests/second
- With API key: 10 requests/second

Agent rules:
1. Use API key whenever available.
2. Respect request rate limits.
3. Backoff/retry on `429` and transient `5xx`.

## 4) Query Format (PubMed/Entrez)

Use PubMed query syntax:
- Boolean: `AND`, `OR`, `NOT`
- Field tags, e.g.:
  - `[Title/Abstract]`
  - `[MeSH Terms]`
  - `[Author]`
- Quoted phrases for exact phrase matching.

Examples:
- `("heat"[Title/Abstract] AND mortality[Title/Abstract])`
- `("climate change"[Title/Abstract] AND heatwave[Title/Abstract])`
- `("Heat Stress Disorders"[MeSH Terms] AND mortality[Title/Abstract])`

## 5) Date and Sort Controls

Supported parameters (pass-through to ESearch):
- `--datetype` (`pdat`, `edat`, `mdat`)
- `--mindate` (e.g. `2015/01/01`)
- `--maxdate` (e.g. `2026/12/31`)
- `--sort` (e.g. `relevance`, `pub_date`)

## 6) Retrieval Strategy (Required)

For large retrieval:
1. Use `usehistory=y` in ESearch.
2. Read `query_key` and `WebEnv`.
3. Pull batches with EFetch using `retstart` + `retmax`.

Do not rely on single massive ID lists in URL for large queries.

## 7) Output Contract

Required outputs:
- `run_summary.json`
- `works_summary.csv`
- `works_full.jsonl`
- `query_runs/*.json`

Important fields in `works_summary.csv`:
- `pmid`
- `doi`
- `title`
- `abstract`
- `journal_title`
- `publication_date`

## 8) Runtime Recommendations

1. Keep `--fetch-batch-size` around `100-500` (default `200`) for stable runs.
2. Set `--max-results-per-query` explicitly to avoid accidental massive jobs.
3. Keep dedup enabled unless per-query duplicates are explicitly required.
4. Include `--email` in production runs for better NCBI compliance.

## 9) Common Failure Modes

1. `429` due to excessive request rate.
2. Empty abstracts for some PMIDs (normal; record has no abstract).
3. Query too broad and retrieval volume too large.
4. Duplicate PMIDs across multiple queries.

## 10) Official References

- E-utilities help: <https://www.ncbi.nlm.nih.gov/books/NBK25501/>
- ESearch: <https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch>
- EFetch: <https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch>
- Quick start: <https://www.ncbi.nlm.nih.gov/books/NBK25500/>
- User-shared NCBI datasets docs: <https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/languages/>
