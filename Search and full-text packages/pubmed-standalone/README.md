# PubMed Standalone Wrapper

Standalone PubMed query wrapper using NCBI E-utilities (`ESearch` + `EFetch`).

Use case:
- Input PubMed query strings
- Retrieve large batches of PubMed metadata
- Export structured results with focus on title + abstract

## 1) Install

```bash
cd /Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/pubmed-standalone
python3 -m pip install -r requirements.txt
```

## 2) Auth and throughput

Set your API key:

```bash
export PUBMED_API_KEY=YOUR_NCBI_API_KEY
```

Optional:

```bash
export PUBMED_EMAIL=your_email@domain.com
```

NCBI rule (from your key management page):
- Without API key: up to 3 requests/second
- With API key: up to 10 requests/second

## 3) Run

### Query file mode (recommended)

```bash
python3 pubmed_search_wrapper.py \
  --query-file sample_queries.txt \
  --max-results-per-query 300 \
  --fetch-batch-size 200 \
  --datetype pdat \
  --mindate 2015/01/01 \
  --out-dir pubmed_run_01
```

### Direct query mode

```bash
python3 pubmed_search_wrapper.py \
  --query '("heat"[Title/Abstract] AND mortality[Title/Abstract])' \
  --query '("climate change"[Title/Abstract] AND heatwave[Title/Abstract])' \
  --max-results-per-query 200 \
  --out-dir pubmed_run_02
```

## 4) Outputs

- `OUT_DIR/run_summary.json`  
  Query-level status, total hits, stored count, API call count
- `OUT_DIR/works_summary.csv`  
  Flattened table with `pmid`, `title`, `abstract`, `doi`, etc.
- `OUT_DIR/works_full.jsonl`  
  Full structured metadata per record
- `OUT_DIR/query_runs/*.json`  
  Per-query API logs (esearch payload + batch info)

## 5) Notes

- Query syntax uses PubMed/Entrez search syntax.
- Wrapper uses `usehistory=y` + `query_key/WebEnv` for scalable retrieval.
- Dedup across multiple queries is enabled by default (by PMID).
- Use `--keep-duplicates` if you need per-query duplicates retained.

## 6) Official docs

- NCBI E-utilities help: <https://www.ncbi.nlm.nih.gov/books/NBK25501/>
- E-utilities quick start: <https://www.ncbi.nlm.nih.gov/books/NBK25500/>
- ESearch details: <https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch>
- EFetch details: <https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch>
- NCBI datasets API docs (you shared): <https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/languages/>
