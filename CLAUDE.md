# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains two major categories of tools for climate intervention and literature review research:

### Legacy Code and Supporting Packages
1. **LLMeta**: Systematic review tool using LLMs with RAG and HyDE techniques
2. **LLMscreen**: Abstract screening tool with OpenAI models
3. **exTweather-hazard**: Sequential climate cascade analysis pipeline (flood → grid failure → heat → health impacts)

### Search and Full-Text Packages
4. **Literature Review Workflow**: Comprehensive system for scientific literature search and full-text retrieval
   - Metadata search wrappers (OpenAlex, PubMed, Scopus)
   - Full-text retrieval chain (Elsevier, Wiley, OpenAlex, Playwright fallback)
   - Content conversion (XML/PDF to Markdown)

## Architecture

### LLMeta (Systematic Reviews)

**Purpose**: Extract variables from scientific literature using LLM-based retrieval augmented generation.

**Core workflow**:
1. Convert PDFs to markdown, split into sections
2. Build FAISS vectorstores with OpenAI embeddings
3. Generate hypothetical text from variable definitions (HyDE)
4. Retrieve relevant document passages
5. Generate judgements and extract variable values
6. Format output to structured CSV

**Key modules**:
- `markdown_to_vectorstore`: Process markdown files into FAISS indexes
- `generate_hypothetical_text`: Create query text from variable definitions
- `get_relate_doc`: Retrieve relevant passages via similarity search
- `generate_judgement`: Extract variable values with confidence scores
- `process_papers`: Parallel processing with ThreadPoolExecutor
- `formated_output`: Merge extractions with metadata

**Entry point**: `example.py`

**Dependencies**: numpy, pandas, openai, langchain, langchain_openai

**API Key**: Required in `api.txt` file

### LLMscreen (Abstract Screening)

**Purpose**: Automated screening of research abstracts against inclusion/exclusion criteria.

**Modes**:
- `simple`: Single-pass JSON decision with probability threshold (parameter `k`)
- `zeroshot`: Chain-of-thought reasoning followed by True/False decision

**Core workflow**:
```python
from LLMscreen import run

df = run(
    csv_file="abstracts.csv",
    filter_criteria="Include studies that focus on XYZ",
    thread=8,
    api_file="api.txt",
    model="gpt-4o-mini-2024-07-18",
    zeroshot=False,
    output_file="result.csv",
)
```

**Input requirements**: CSV with `title` and/or `abstract` columns

**Output schema**: Fixed columns including `judgement`, `reason`, `n_probability`, `perplexity_score`, `token_probability`, `error`

**Module structure**:
- `client.py`: OpenAI client setup
- `prompts.py`: Prompt construction
- `scoring.py`: Probability and perplexity metrics
- `pipeline.py`: Threaded orchestration

### exTweather-hazard (Climate Cascade Pipeline)

**Purpose**: Quantify health impacts from sequential flood-then-heat events with infrastructure failure.

**Four-layer cascade**:
1. **Hazard layer**: Flood + heat extremes, sequential event detection
2. **Infrastructure layer**: Grid exposure and outage probability
3. **Health layer**: Temperature-mortality curves with adaptation failure
4. **Economics layer**: Valuation and IAM comparison

**Pipeline stages** (in execution order):
1. `ingest_hazard`: Process flood data (GloFAS/JRC) and reanalysis (ERA5-Land)
2. `detect_sequential`: Identify flood→heat event sequences with time windows
3. `outage_probability`: Compute grid failure risk from flood depth + fragility curves
4. `health_response`: Build baseline/failure temperature-mortality curves (DLNM)
5. `coupling`: Combine outage probability with health response
6. `valuation`: Monetize impacts using VSL

**Module boundaries**:
- `src/hazard/`: `flood.py`, `heat.py`, `sequential.py`
- `src/infrastructure/`: `grid.py`, `outage.py`
- `src/health/`: `dlnm.py`, `mortality.py`
- `src/coupling/`: `adaptation.py`, `aggregate.py`
- `src/economics/`: `valuation.py`
- `src/pipeline/`: `stages.py` (stage registry), `run.py` (CLI entry)
- `src/utils/`: `config.py`, `data_paths.py`, `geo.py`, `time.py`

**Configuration**: JSON files in `configs/` directory
- `configs/params.json`: Model parameters
- `configs/paths.json`: File paths
- `configs/sources.json`: Data source definitions
- `data_paths.json`: Runtime data paths (repo root)

### Literature Review Workflow

**Purpose**: End-to-end system for scientific literature discovery and full-text acquisition.

**Three-stage workflow**:
1. **Query generation**: User defines search queries (not in repo)
2. **Metadata search**: Execute queries against academic databases
3. **Full-text retrieval**: Download content with fallback chain

**Architecture location**: `Search and full-text packages/`

#### Metadata Search Wrappers (Standalone)

Each wrapper is independent with common output schema:
- `run_summary.json`: Query-level stats and errors
- `works_summary.csv`: Flattened table (title, abstract, DOI, etc.)
- `works_full.jsonl`: Full metadata payloads
- `query_runs/*.json`: Raw per-query API logs

**Available wrappers**:

1. **OpenAlex Standalone** (`openalex-standalone/`)
   - `openalex_metadata_wrapper.py`: DOI → metadata singleton lookup
   - `openalex_search_wrapper.py`: Query → large batch retrieval (paginated)
   - `openalex_content_wrapper.py`: Work/DOI → PDF/TEI-XML download
   - Supports semantic search mode (limited to ~50 results)
   - Content API cost: $0.01 per file

2. **PubMed Standalone** (`pubmed-standalone/`)
   - `pubmed_search_wrapper.py`: NCBI E-utilities (ESearch + EFetch)
   - Query syntax: PubMed/Entrez format
   - Rate limits: 3 req/s (no key), 10 req/s (with key)
   - Uses `usehistory=y` for scalable batch retrieval

3. **Elsevier Standalone** (`elsevier-standalone/`)
   - `downloader.py`: Elsevier API direct download
   - `publisher_downloader.py`: Unified Elsevier + Wiley + auto-detect
   - Supports institutional tokens for entitlement
   - Status: `success`, `success_limited` (first-page-only)

4. **Search Packages** (`search-packages/`)
   - Zipped portable versions: `openalex-searcher`, `pubmed-searcher`, `scopus-searcher`
   - Same output contract as standalone wrappers

#### Full-Text Retrieval Chain

**Module**: `fulltext-packages/fulltext_chain_wrapper.py`

**Retrieval strategy** (in priority order):
1. OpenAlex content API (OA-first, reduces publisher API cost)
2. Publisher APIs (Elsevier XML, Wiley PDF)
3. Playwright browser fallback (last resort, less deterministic)

**Content conversion**:
- XML → Markdown: Built-in (Elsevier XML)
- PDF → Markdown: MinerU (preferred) or fallback (pypdf/PyMuPDF)
- Placeholder generation for OCR-required PDFs

**Output structure**:
- `downloads/elsevier/*.xml`
- `downloads/wiley/*.pdf`
- `downloads/openalex/*.pdf`
- `downloads/playwright/*.pdf`
- `md/...` (when `--convert-to-md` enabled)
- `results.csv`, `results.json`, `run_summary.json`

## Common Commands

### LLMeta
```bash
# Install package
cd "Legacy code and supporting packages/LLMeta-main"
pip install -e .

# Run example workflow
python example.py
```

### LLMscreen
```bash
# Install package
cd "Legacy code and supporting packages/LLMscreen"
pip install LLMscreen

# Run screening (see Quick Start in LLMscreen/README.md)
```

### exTweather-hazard

```bash
cd "Legacy code and supporting packages/exTweather-hazard"

# Dry run (print stages without execution)
python3 scripts/run_pipeline.py --config-dir configs --dry-run

# Run single stage
python3 scripts/run_pipeline.py --stage detect_sequential

# Validate data paths
python3 scripts/check_data.py

# Download CDS data (ERA5-Land sample)
python3 scripts/download_cds.py \
  --product reanalysis-era5-land \
  --request configs/cds_requests/era5_land_sample.json \
  --target data/raw/climate/era5_land/era5_sample.nc

# Download OSM substations
python3 scripts/download_osm_substations.py \
  --bbox "20,100,30,110" \
  --output data/raw/grid/osm/substations.json

# Literature data extraction
python3 scripts/ingest_literature_data.py --extract-tables --extract-snippets
python3 scripts/structure_literature_snippets.py
```

### OpenAlex Standalone

```bash
cd "Search and full-text packages/openalex-standalone"

# Install dependencies
pip install -r requirements.txt

# Set credentials (recommended)
export OPENALEX_API_KEY=YOUR_KEY
export OPENALEX_MAILTO=your@email.com

# Metadata lookup by DOI
python3 openalex_metadata_wrapper.py \
  --doi 10.1038/nature12373 \
  --out-dir test_metadata

# Search with queries
python3 openalex_search_wrapper.py \
  --query-file sample_queries.txt \
  --max-results-per-query 300 \
  --filter 'type:article,from_publication_date:2015-01-01' \
  --out-dir search_run

# Content download (PDF/XML)
python3 openalex_content_wrapper.py \
  --work-id W4383823379 \
  --content-types pdf,xml \
  --out-dir content_run
```

### PubMed Standalone

```bash
cd "Search and full-text packages/pubmed-standalone"

# Install dependencies
pip install -r requirements.txt

# Set credentials
export PUBMED_API_KEY=YOUR_NCBI_KEY
export PUBMED_EMAIL=your@email.com

# Search with queries
python3 pubmed_search_wrapper.py \
  --query-file sample_queries.txt \
  --max-results-per-query 300 \
  --datetype pdat \
  --mindate 2015/01/01 \
  --out-dir pubmed_run
```

### Elsevier/Wiley Standalone

```bash
cd "Search and full-text packages/elsevier-standalone"

# Set credentials
export ELSEVIER_API_KEY=YOUR_KEY
export ELSEVIER_INST_TOKEN=YOUR_INSTTOKEN  # optional
export WILEY_TDM_CLIENT_TOKEN=YOUR_WILEY_TOKEN

# Elsevier download
python3 downloader.py \
  --doi-file sample_dois.csv \
  --out-dir elsevier_downloads

# Unified publisher download (auto-detect)
python3 publisher_downloader.py \
  --publisher auto \
  --doi-file mixed_dois.csv \
  --out-dir publisher_downloads
```

### Full-Text Retrieval Chain

```bash
cd "Search and full-text packages/fulltext-packages"

# Install dependencies
pip install -r requirements.txt

# Optional: Playwright for browser fallback
python3 -m playwright install chromium

# Optional: MinerU for advanced PDF conversion
pip install "mineru[all]"

# Set all credentials
export OPENALEX_API_KEY=YOUR_KEY
export OPENALEX_MAILTO=your@email.com
export ELSEVIER_API_KEY=YOUR_KEY
export ELSEVIER_INST_TOKEN=YOUR_INSTTOKEN  # optional
export WILEY_TDM_CLIENT_TOKEN=YOUR_WILEY_TOKEN

# Run full-text chain (OA → Publishers → Playwright)
python3 fulltext_chain_wrapper.py \
  --doi-file sample_dois.csv \
  --convert-to-md \
  --use-playwright-fallback \
  --out-dir fulltext_run

# Without browser fallback
python3 fulltext_chain_wrapper.py \
  --doi-file sample_dois.csv \
  --convert-to-md \
  --out-dir fulltext_run_no_browser
```

## Data Flow

### exTweather-hazard Data Pipeline

**Raw data** → **Interim grids** → **Event detection** → **Impact assessment** → **Outputs**

Key data products:
- `data/raw/`: Original datasets (flood, reanalysis, grid assets)
- `data/interim/`: Harmonized grids and time series
- `data/processed/`: Sequential event masks, outage probability, mortality curves
- `data/outputs/`: Aggregated impacts, figures, tables

### Data Sources (see `docs/data_sources.md` and `docs/pipeline_design.md`)
- **Flood**: GloFAS (CDS), JRC Global Flood Hazard Maps
- **Climate**: ERA5-Land (CDS)
- **Grid**: OSM substations via Overpass API
- **Population**: GHS-POP (JRC)
- **Health**: DLNM coefficients from MCC framework
- **Literature**: Extracted tables and snippets from mined PDFs

### Literature Review Data Flow

**Query → Metadata → Full-Text → Analysis**

#### Stage 2: Metadata Search Outputs
All search wrappers (OpenAlex, PubMed, Elsevier) produce:
- `run_summary.json`: Query execution stats, counts, errors
- `works_summary.csv`: Flattened table with key fields (title, abstract, DOI, authors, year)
- `works_full.jsonl`: Complete metadata (one JSON object per line)
- `query_runs/*.json`: Per-query raw API responses

#### Stage 3: Full-Text Retrieval Outputs
Full-text chain produces:
- `results.csv` / `results.json`: Per-DOI status and metadata
- `run_summary.json`: Execution summary with estimated costs
- `downloads/`:
  - `elsevier/*.xml`: Elsevier full-text XML
  - `wiley/*.pdf`: Wiley PDFs
  - `openalex/*.pdf`: OpenAlex OA PDFs
  - `playwright/*.pdf`: Browser-fallback PDFs
- `md/`: Converted markdown files (when `--convert-to-md`)
  - `elsevier/*.md`: From XML
  - `wiley/*.md`, `openalex/*.md`, `playwright/*.md`: From PDF

#### Deduplication
- Search wrappers deduplicate by PMID (PubMed) or DOI (OpenAlex, Elsevier)
- Use `--keep-duplicates` to retain per-query duplicates

## Development Notes

### API Keys

**LLM-based tools** (LLMeta, LLMscreen):
- OpenAI API keys stored in `api.txt` files in their respective directories

**Literature review tools** (all use environment variables):
```bash
# OpenAlex
export OPENALEX_API_KEY=YOUR_KEY
export OPENALEX_MAILTO=your@email.com

# PubMed (NCBI E-utilities)
export PUBMED_API_KEY=YOUR_NCBI_KEY
export PUBMED_EMAIL=your@email.com

# Elsevier
export ELSEVIER_API_KEY=YOUR_KEY
export ELSEVIER_INST_TOKEN=YOUR_INSTTOKEN  # optional, for institutional access

# Wiley
export WILEY_TDM_CLIENT_TOKEN=YOUR_WILEY_TOKEN
```

**Security policy**:
- Never hardcode API keys in scripts or commit them to version control
- Use environment variables or pass keys via CLI arguments
- Keep institutional tokens server-side only (never in URLs or browser code)

### Proxy Configuration
Example scripts show proxy configuration via environment variables:
```python
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'
```

### Pipeline Extension
To add new pipeline stages in exTweather-hazard:
1. Define stage function in `src/pipeline/stages.py`
2. Add to `STAGES` list with inputs/outputs
3. Implement module logic in appropriate `src/` subdirectory

### CDS Data Access
Requires `.cdsapirc` file in project root for Copernicus Climate Data Store access (ERA5-Land, GloFAS). See `docs/data_ingest.md` for setup checklist.

### Stage Status
The exTweather-hazard pipeline stages raise `NotImplementedError` - this is a skeleton awaiting implementation of the full cascade model.

### Literature Review Setup

**Basic dependencies** (all search/fulltext wrappers):
```bash
pip install requests tqdm pandas
```

**Optional: Playwright browser automation** (for fulltext-chain fallback):
```bash
pip install playwright
python3 -m playwright install chromium
```

**Optional: MinerU PDF conversion** (for advanced PDF → Markdown):
```bash
pip install "mineru[all]"
```

**Fallback PDF extraction**: If MinerU unavailable, wrappers use `pypdf` or `PyMuPDF`

**Rate limits**:
- OpenAlex: No limit with key, recommended for politeness
- PubMed: 3 req/s (no key), 10 req/s (with key)
- Elsevier: Varies by contract, use `--max-retries` for 429 handling
- Wiley: Check TDM service agreement
