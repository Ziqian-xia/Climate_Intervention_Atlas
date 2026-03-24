# OpenAlex Standalone Wrappers

This folder has two wrappers:

1. `openalex_metadata_wrapper.py` (DOI -> metadata singleton retrieval)
2. `openalex_search_wrapper.py` (search query -> large batch metadata retrieval)
3. `openalex_content_wrapper.py` (work/doi -> content download: PDF/TEI XML)

All wrappers export structured outputs for workflow integration.

## A) DOI Metadata Wrapper

Fetch OpenAlex **full work metadata** by DOI, with explicit exports for:

- Title
- Reconstructed abstract text
- Raw full metadata JSON

## 1) Install

```bash
cd /Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/openalex-standalone
python3 -m pip install -r requirements.txt
```

## 2) Auth (recommended)

OpenAlex works without a key for basic usage, but key + mailto are recommended for better reliability and limits.

```bash
export OPENALEX_API_KEY=YOUR_OPENALEX_API_KEY
export OPENALEX_MAILTO=your_email@domain.com
```

## 3) Run

Single DOI:

```bash
python3 openalex_metadata_wrapper.py \
  --doi 10.1038/nature12373 \
  --out-dir test_openalex
```

Multiple DOIs:

```bash
python3 openalex_metadata_wrapper.py \
  --doi 10.1038/nature12373 \
  --doi 10.1016/j.oneear.2026.101624 \
  --out-dir test_openalex
```

From file:

```bash
python3 openalex_metadata_wrapper.py \
  --doi-file sample_dois.csv \
  --doi-column doi \
  --out-dir test_openalex
```

## 4) Outputs

- `OUT_DIR/results.json`: summary for each DOI
- `OUT_DIR/results.csv`: table view (includes title + reconstructed abstract)
- `OUT_DIR/metadata_full.jsonl`: full metadata payloads (one line per work)
- `OUT_DIR/raw_works/*.json`: full metadata JSON per DOI

### Notes

- DOI lookup uses OpenAlex external-id singleton route: `works/doi:{doi}`
- Abstract is reconstructed from `abstract_inverted_index`
- Retries are built-in for `429` and transient `5xx`

## B) Search Wrapper (Workflow Step-2)

Use this after generating search queries. Input OpenAlex-format query strings and fetch many works.

Example using repeated `--query`:

```bash
python3 openalex_search_wrapper.py \
  --api-key "$OPENALEX_API_KEY" \
  --mailto "$OPENALEX_MAILTO" \
  --search-param search \
  --query '"heat" AND mortality' \
  --query '"climate change" AND heatwave AND mortality' \
  --filter 'type:article,from_publication_date:2015-01-01' \
  --sort relevance_score:desc \
  --max-results-per-query 300 \
  --out-dir search_run_01
```

Example from query file (`txt/csv/json/jsonl`):

```bash
python3 openalex_search_wrapper.py \
  --query-file sample_queries.txt \
  --query-column query \
  --max-results-per-query 500 \
  --out-dir search_run_file
```

Search outputs:

- `OUT_DIR/run_summary.json`: query-level status/cost/stats
- `OUT_DIR/works_summary.csv`: flattened table including title + abstract
- `OUT_DIR/works_full.jsonl`: full metadata for each stored work
- `OUT_DIR/query_runs/*.json`: raw per-query responses

Semantic mode note:
- `--search-param search.semantic` uses basic page pagination (not cursor).
- OpenAlex semantic API currently limits this path to up to ~50 results.

## C) Content Wrapper (Workflow Step-3)

Use this after step-2 when you already have OpenAlex IDs/DOIs and want possible full text content.

Official content endpoint:
- `https://content.openalex.org/works/{work_id}.pdf?api_key=YOUR_KEY`
- `https://content.openalex.org/works/{work_id}.grobid-xml?api_key=YOUR_KEY`

Pricing note (official): each content file download costs `$0.01`.

### Example: direct IDs

```bash
python3 openalex_content_wrapper.py \
  --api-key "$OPENALEX_API_KEY" \
  --work-id W4383823379 \
  --content-types pdf \
  --out-dir content_run_01
```

### Example: PDF + XML from file

```bash
python3 openalex_content_wrapper.py \
  --api-key "$OPENALEX_API_KEY" \
  --id-file sample_content_ids.csv \
  --work-id-column openalex_id \
  --doi-column doi \
  --content-types pdf,xml \
  --skip-existing \
  --out-dir content_run_file
```

### Example: directly from step-2 output

```bash
python3 openalex_content_wrapper.py \
  --api-key "$OPENALEX_API_KEY" \
  --from-works-summary search_run_01/works_summary.csv \
  --content-types pdf \
  --max-targets 500 \
  --out-dir content_from_step2
```

Content outputs:

- `OUT_DIR/files/pdf/*.pdf`
- `OUT_DIR/files/grobid_xml/*.xml` or `*.xml.gz` (some responses are gzip-compressed)
- `OUT_DIR/raw_work_metadata/*.json`
- `OUT_DIR/results.csv`
- `OUT_DIR/results.json`
- `OUT_DIR/run_summary.json` (includes estimated cost by attempts/successes)
