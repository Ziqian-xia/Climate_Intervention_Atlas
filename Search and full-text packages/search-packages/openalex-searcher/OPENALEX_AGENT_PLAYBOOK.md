# OpenAlex Agent Playbook

Last updated: 2026-03-23  
Scope: How agents should run OpenAlex retrieval with this package.

## 1) Workflow Role

Use this wrapper after query generation and before full-text/content retrieval.

Flow:
1. Upstream step generates OpenAlex-compatible query strings.
2. Agent runs `openalex_search_wrapper.py`.
3. Downstream step consumes `works_summary.csv` and `works_full.jsonl`.

## 2) API Endpoint Pattern

Wrapper targets:
- `GET https://api.openalex.org/works`

Supported search parameters:
- `search`
- `search.exact`
- `search.semantic`

## 3) Authentication and Cost Signals

Recommended runtime auth inputs:
- `OPENALEX_API_KEY`
- `OPENALEX_MAILTO`

OpenAlex responses include metadata like `meta.count`, `meta.next_cursor`, and often cost signal fields (`meta.cost_usd`), which the wrapper aggregates at query level.

## 4) Query Input Contract

Agent may pass queries via:
- repeated `--query`
- or `--query-file` in `txt/csv/json/jsonl`

For object-based files (`csv/json/jsonl`), query field defaults to `query` and can be changed by `--query-column`.

## 5) Paging Rules

- `search` and `search.exact`: cursor pagination (`cursor=*`, then `next_cursor`)
- `search.semantic`: page pagination only (`page/per_page`), no cursor mode

Operational implication:
- semantic mode is for targeted testing/smaller retrievals
- large retrieval should use `search`

## 6) Dedup and Record Mapping

Dedup key:
- `openalex_id` (`work.id`)

Default behavior:
- deduplicate across all queries

Disable with:
- `--keep-duplicates`

Important transforms:
- DOI normalized from URL/prefix form to canonical lowercase DOI
- abstract reconstructed from `abstract_inverted_index`

## 7) Output Contract

Required outputs:
- `run_summary.json`
- `works_summary.csv`
- `works_full.jsonl`
- `query_runs/*.json`

Key fields to rely on in `works_summary.csv`:
- `openalex_id`
- `doi`
- `title`
- `abstract`
- `publication_year`
- `type`
- `cited_by_count`
- `is_oa`

## 8) Failure Handling

Built-in behavior:
- retries on `429` and transient `5xx`
- exponential backoff with optional `Retry-After`

Common failure reasons:
1. malformed filter/sort syntax
2. semantic mode expectations mismatched with cursor behavior
3. overly broad query causing large runtime and quota spend

## 9) Recommended Runtime Defaults

For production-scale metadata pull:
1. `--search-param search`
2. set explicit `--max-results-per-query`
3. retain dedup unless duplicates are explicitly needed
4. set `--mailto` in all non-local runs

## 10) Official References

- Overview: <https://developers.openalex.org/>
- Searching: <https://developers.openalex.org/guides/searching>
- Paging: <https://developers.openalex.org/guides/page-through-results>
- Filters: <https://developers.openalex.org/api-entities/works/filter-works>
