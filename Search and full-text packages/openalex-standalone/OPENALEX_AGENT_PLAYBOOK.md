# OpenAlex Agent Playbook (Search + Content)

Last updated: 2026-03-22  
Scope: How future agents should run OpenAlex search (step-2) and content download (step-3) safely.

## 1) Purpose in This Workflow

This is **workflow step-2**:
1. Upstream system generates OpenAlex-style search queries.
2. Agent runs OpenAlex search API to collect large batches of works metadata.
3. Agent exports both:
   - Full metadata (for downstream analytics)
   - Flattened title/abstract table (for screening and triage)

Use local wrapper:
- `openalex_search_wrapper.py` for query-based retrieval
- `openalex_metadata_wrapper.py` for DOI singleton retrieval
- `openalex_content_wrapper.py` for PDF/TEI content download

## 2) Base URL and Authentication

- Base URL: `https://api.openalex.org`
- Recommended auth: `api_key=YOUR_KEY`
- Recommended contact: `mailto=you@domain`

Environment variables used in this repo:
- `OPENALEX_API_KEY`
- `OPENALEX_MAILTO`

Official docs:
- Overview: <https://developers.openalex.org/>
- Authentication & Pricing: <https://developers.openalex.org/api-reference/authentication>

## 3) Search Parameters (Core)

Use exactly one of:
- `search`
- `search.exact`
- `search.semantic`

Do **not** combine them in one request.

### 3.1 `search` (default keyword/full-text)
- Works searches over: `title`, `abstract`, `fulltext`
- Supports stemming and stop-word removal

### 3.2 `search.exact`
- Unstemmed exact term matching behavior

### 3.3 `search.semantic` (beta)
- Embedding-based semantic retrieval
- Additional constraints apply:
  - cursor pagination is not supported
  - basic paging is used
  - API response indicates max retrieval around 50 results for this mode

Official doc:
- Search guide: <https://developers.openalex.org/guides/searching>

## 4) Query Syntax Rules for Agents

### 4.1 Boolean operators
- Allowed: `AND`, `OR`, `NOT` (uppercase)
- Terms without explicit operators are treated as `AND`

Example:
- `(heat AND mortality) NOT ("animal model" OR mice)`

### 4.2 Phrases
- Use double quotes for exact phrase matching
- Example: `"heat-related mortality"`

### 4.3 Proximity
- Use `"phrase"~N`
- Example: `"climate change"~5`

### 4.4 Wildcards
- `*` = zero or more chars, `?` = one char
- At least 3 chars before wildcard
- Leading wildcard not supported (no `*ology`)

### 4.5 Fuzzy term match
- `term~N` where `N` in `{0,1,2}`
- At least 3 chars before `~`

Official doc:
- Search syntax details: <https://developers.openalex.org/guides/searching>

## 5) Filters, Sorting, and Field Selection

### 5.1 Filter (`filter=`)
- Comma = AND across filters
- `|` = OR within one filter (max 100 values)
- `!` = NOT
- Supports numeric inequality (`>`, `<`) on numeric filters

Example:
- `filter=type:article,from_publication_date:2015-01-01`
- `filter=doi:https://doi.org/10.x/a|https://doi.org/10.x/b`

Doc:
- Filtering: <https://developers.openalex.org/guides/filtering>

### 5.2 Sort (`sort=`)
- Typical form: `sort=relevance_score:desc` or `sort=cited_by_count:desc`

### 5.3 Select (`select=`)
- Use to reduce payload size.
- Root-level fields only (nested like `open_access.is_oa` is invalid in `select`).

Doc:
- Select fields: <https://developers.openalex.org/guides/selecting-fields>

## 6) Pagination Rules (Critical)

### 6.1 Basic paging
- `page` + `per_page`
- `per_page` max = `100`
- Basic paging can only reach first `10,000` results

### 6.2 Cursor paging (required for large retrieval)
1. Start with `cursor=*`
2. Read `meta.next_cursor`
3. Continue until `next_cursor` is `null` and results are empty

Doc:
- Paging: <https://developers.openalex.org/guides/page-through-results>

Exception:
- `search.semantic` must use basic paging (`page/per_page`), not cursor.

## 7) Cost and Rate Limits (Agent Behavior)

From Authentication & Pricing docs:
- API key has daily free budget (`$1/day`)
- Search calls are more expensive than list+filter
- Too many requests -> `429`
- Query limits include:
  - `per_page <= 100`
  - OR values per filter <= 100
  - sample <= 10,000
  - basic paging <= 10,000 results

Required agent behavior:
1. Always set `per_page=100` for bulk extraction.
2. Prefer filter-based retrieval when possible (cheaper than full-text search).
3. Implement exponential backoff on `429` and transient `5xx`.
4. Track `meta.cost_usd` and `meta.count` to estimate full-run cost early.

Doc:
- Auth/pricing/limits: <https://developers.openalex.org/api-reference/authentication>

## 8) Required Output Contract for This Repo

When running `openalex_search_wrapper.py`, agents must produce:
- `run_summary.json` (query-level status, call count, cost)
- `works_summary.csv` (flattened, includes `title`, reconstructed `abstract`)
- `works_full.jsonl` (full metadata per work)
- `query_runs/*.json` (raw query responses)

For DOI singleton mode (`openalex_metadata_wrapper.py`):
- `results.json`, `results.csv`
- `metadata_full.jsonl`
- `raw_works/*.json`

For content mode (`openalex_content_wrapper.py`):
- `files/pdf/*.pdf`
- `files/grobid_xml/*.xml` or `*.xml.gz`
- `raw_work_metadata/*.json`
- `results.json`, `results.csv`
- `run_summary.json` (attempts, successes, estimated cost)

## 9) Content API (Workflow Step-3)

Official content API:
- `https://content.openalex.org/works/{work_id}.pdf?api_key=YOUR_KEY`
- `https://content.openalex.org/works/{work_id}.grobid-xml?api_key=YOUR_KEY`

Key points from official docs:
1. Content API is designed for file-by-file download (good up to ~10k files).
2. Each content file download costs `$0.01`.
3. Use `has_content` filters on metadata API to preselect downloadable works:
   - `has_content.pdf:true`
   - `has_content.grobid_xml:true` (field name in work object is `has_content.grobid_xml`)
4. For license-sensitive workflows, filter/check:
   - `best_oa_location.license`

Required agent behavior for content runs:
1. Pre-filter target works whenever possible to reduce paid misses.
2. Persist per-file download status (`success/http_404/http_401/...`).
3. Persist metadata snapshot per work for reproducibility.
4. Report cost estimates:
   - attempts * $0.01
   - successful files * $0.01

Official doc:
- Full-text PDFs / Content API: <https://developers.openalex.org/download/full-text-pdfs>

## 10) Recommended Minimal Request Templates

### 10.1 Query search (step-2)
```bash
OPENALEX_API_KEY='YOUR_KEY' OPENALEX_MAILTO='you@org.edu' \
python3 openalex_search_wrapper.py \
  --search-param search \
  --query '"heat" AND mortality' \
  --filter 'type:article,from_publication_date:2015-01-01' \
  --sort relevance_score:desc \
  --max-results-per-query 1000 \
  --out-dir run_step2
```

### 10.2 Query file batch
```bash
python3 openalex_search_wrapper.py \
  --query-file sample_queries.txt \
  --query-column query \
  --max-results-per-query 1000 \
  --out-dir run_step2_file
```

### 10.3 DOI singleton metadata
```bash
python3 openalex_metadata_wrapper.py \
  --doi 10.1371/journal.pone.0266781 \
  --out-dir run_singleton
```

### 10.4 Content download (step-3)
```bash
OPENALEX_API_KEY='YOUR_KEY' \
python3 openalex_content_wrapper.py \
  --from-works-summary run_step2/works_summary.csv \
  --content-types pdf,xml \
  --max-targets 500 \
  --skip-existing \
  --out-dir run_step3_content
```

## 11) Common Mistakes to Avoid

1. Using `page` for deep retrieval >10k results instead of cursor paging.
2. Mixing `search` with `search.exact`/`search.semantic` in one call.
3. Overusing expensive search when equivalent `filter` exists.
4. Assuming every work has reconstructable abstract (`abstract_inverted_index` can be empty).
5. Exposing API keys in code or committed config files.
6. Downloading content blindly without checking `has_content` or license policy.
7. Using cursor pagination with `search.semantic`.

## 12) Source Links (Official)

- OpenAlex docs home: <https://developers.openalex.org/>
- Search: <https://developers.openalex.org/guides/searching>
- Filter: <https://developers.openalex.org/guides/filtering>
- Paging: <https://developers.openalex.org/guides/page-through-results>
- Select fields: <https://developers.openalex.org/guides/selecting-fields>
- Authentication & pricing: <https://developers.openalex.org/api-reference/authentication>
- Full-text PDFs / content API: <https://developers.openalex.org/download/full-text-pdfs>
