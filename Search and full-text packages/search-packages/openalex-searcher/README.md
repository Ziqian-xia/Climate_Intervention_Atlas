# OpenAlex Searcher

Standalone OpenAlex metadata search package.

## Purpose

`openalex_search_wrapper.py` executes OpenAlex query strings and exports structured metadata for downstream workflows, with strong focus on title + abstract availability.

## Install

```bash
cd /Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/search-packages/openalex-searcher
python3 -m pip install -r requirements.txt
```

## Authentication

OpenAlex supports API key + contact email.

```bash
export OPENALEX_API_KEY="YOUR_OPENALEX_KEY"
export OPENALEX_MAILTO="your_email@domain.com"
```

## Query Modes

Choose one of:
- `search`: keyword search (recommended for broad retrieval)
- `search.exact`: exact phrase search
- `search.semantic`: semantic retrieval (limited depth, no cursor mode)

## Basic Run

```bash
python3 openalex_search_wrapper.py \
  --search-param search \
  --query-file sample_queries.txt \
  --max-results-per-query 1000 \
  --out-dir run_openalex
```

## Key CLI Options

- `--query` (repeatable) and/or `--query-file` (`txt/csv/json/jsonl`)
- `--filter` and `--sort` (OpenAlex-native)
- `--select` to limit root fields
- `--per-page` (1-100; semantic mode internally capped lower)
- `--keep-duplicates` to keep duplicated OpenAlex IDs across queries

## Outputs

- `run_summary.json`
- `works_summary.csv`
- `works_full.jsonl`
- `query_runs/*.json`

Primary CSV columns:
- `openalex_id`, `doi`, `title`, `abstract`, `publication_year`, `type`, `cited_by_count`, `is_oa`

## Notes

- `search.semantic` uses `page/per_page`, not cursor pagination.
- For large-scale retrieval, prefer `--search-param search`.
- Abstracts are reconstructed from `abstract_inverted_index`.

## Docs

- OpenAlex docs: <https://developers.openalex.org/>
- Searching guide: <https://developers.openalex.org/guides/searching>
