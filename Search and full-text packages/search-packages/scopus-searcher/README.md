# Scopus Searcher

Standalone Scopus metadata search package via Elsevier Scopus Search API.

## Purpose

`scopus_search_wrapper.py` executes Scopus query strings (for example `TITLE-ABS-KEY(...)`), paginates through results, and exports normalized metadata tables plus full JSON entries.

## Install

```bash
cd /Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/search-packages/scopus-searcher
python3 -m pip install -r requirements.txt
```

## Authentication

Required:
- Elsevier API key with Scopus entitlement

Optional:
- institution token for institutional entitlement context

```bash
export ELSEVIER_API_KEY="YOUR_ELSEVIER_KEY"
export ELSEVIER_INST_TOKEN="YOUR_INSTTOKEN_OPTIONAL"
```

## Query Syntax

Use Scopus search syntax, typically:
- `TITLE-ABS-KEY(heat AND mortality)`
- `TITLE-ABS-KEY("tropical cyclone" AND "mental health")`

## Basic Run

```bash
python3 scopus_search_wrapper.py \
  --query-file sample_queries.txt \
  --max-results-per-query 1000 \
  --count-per-page 25 \
  --out-dir run_scopus
```

## Key CLI Options

- `--query` (repeatable) and/or `--query-file` (`txt/csv/json/jsonl`)
- `--view` (optional API view)
- `--count-per-page` (1-200)
- `--requests-per-second` to override default throttle
- `--keep-duplicates` to keep duplicate EIDs across queries

## Outputs

- `run_summary.json`
- `works_summary.csv`
- `works_full.jsonl`
- `query_runs/*.json`

Primary CSV columns:
- `eid`, `doi`, `title`, `description`, `creator`, `publication_name`, `cover_date`, `citedby_count`

## Notes

- Header auth is used (`X-ELS-APIKey`, optional `X-ELS-Insttoken`).
- Wrapper retries on `429` and transient `5xx`.
- `run_summary.json` includes `x_els_status` for troubleshooting entitlement/rate-limit behavior.

## Docs

- Elsevier Developer Portal: <https://dev.elsevier.com/>
- Scopus Search tips: <https://dev.elsevier.com/sc_search_tips.html>
