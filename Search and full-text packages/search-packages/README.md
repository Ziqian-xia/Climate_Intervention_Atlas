# Literature Search Packages (Scopus / OpenAlex / PubMed)

This folder contains three standalone metadata search wrappers for workflow step-2 (query execution).

Each package is independent and includes:
- one executable Python wrapper
- `requirements.txt`
- sample query file
- user README
- agent playbook

## Package Map

- `openalex-searcher/`: OpenAlex works search (title/abstract-rich metadata)
- `pubmed-searcher/`: PubMed E-utilities search + fetch (PMID records and abstracts)
- `scopus-searcher/`: Scopus Search API metadata retrieval (Elsevier)

## Shared Output Contract

All three wrappers generate the same output structure:
- `run_summary.json`: query-level status, counts, and errors
- `works_summary.csv`: flattened table for fast review and downstream filtering
- `works_full.jsonl`: full metadata payload per stored record
- `query_runs/*.json`: raw per-query API logs

## Quick Start

```bash
cd /Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/search-packages/<package-name>
python3 -m pip install -r requirements.txt
python3 <wrapper.py> --query-file sample_queries.txt --max-results-per-query 200 --out-dir run_demo
```

See each package README for API keys, query syntax, and provider-specific limits.
