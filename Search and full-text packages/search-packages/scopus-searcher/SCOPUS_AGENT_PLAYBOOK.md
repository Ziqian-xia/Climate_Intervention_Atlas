# Scopus Agent Playbook

Last updated: 2026-03-23  
Scope: How agents should run Scopus metadata retrieval in this package.

## 1) Workflow Role

Use Scopus as a metadata search backend after query generation.

Flow:
1. Upstream step creates Scopus syntax query strings.
2. Agent runs `scopus_search_wrapper.py`.
3. Downstream steps use deduplicated metadata outputs.

## 2) API and Authentication

Endpoint:
- `GET https://api.elsevier.com/content/search/scopus`

Auth headers:
- `X-ELS-APIKey` (required)
- `X-ELS-Insttoken` (optional, institutional entitlement context)

Agent security rule:
- never hardcode API key or insttoken in code
- pass via env vars or runtime CLI arguments

## 3) Query Contract

Expected query syntax follows Scopus language (for example):
- `TITLE-ABS-KEY(heat AND mortality)`
- `TITLE-ABS-KEY("climate change" AND heatwave AND mortality)`

Input methods:
- repeated `--query`
- or `--query-file` in `txt/csv/json/jsonl`
- use `--query-column` for object-based files when field name is not `query`

## 4) Paging and Throughput

Pagination model:
- `start` + `count` parameters

Wrapper controls:
- `--count-per-page` (1-200)
- `--max-results-per-query`
- `--requests-per-second` for throttle override

Default behavior is conservative throttling with retry/backoff for `429` and transient `5xx`.

## 5) Dedup and Output Identity

Dedup key:
- `eid`

Default:
- deduplicate across all queries

Disable with:
- `--keep-duplicates`

## 6) Output Contract

Required outputs:
- `run_summary.json`
- `works_summary.csv`
- `works_full.jsonl`
- `query_runs/*.json`

Fields to use in `works_summary.csv`:
- `eid`
- `doi`
- `title`
- `description`
- `creator`
- `publication_name`
- `cover_date`
- `citedby_count`

## 7) Common Failure Modes

1. `401` invalid API key or key without Scopus entitlement
2. `403` authorization/entitlement issue
3. `429` rate-limit exceeded
4. query syntax mismatch with Scopus grammar

Always inspect:
- `run_summary.json` status/error fields
- `x_els_status` response header snapshot in summary
- per-query raw logs under `query_runs/`

## 8) Recommended Runtime Defaults

1. Keep `--count-per-page` between `25` and `100` for stability.
2. Set explicit `--max-results-per-query`.
3. Keep dedup enabled unless per-query duplicate accounting is needed.
4. Use insttoken only in server-side secure environments.

## 9) Official References

- Elsevier Developer Portal: <https://dev.elsevier.com/>
- Scopus Search tips: <https://dev.elsevier.com/sc_search_tips.html>
