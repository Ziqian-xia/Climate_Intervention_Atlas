# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Repository Overview

This repository contains three Python packages for climate intervention and literature review research:

1. **LLMeta**: Systematic review tool using LLMs with RAG and HyDE techniques
2. **LLMscreen**: Abstract screening tool with OpenAI models
3. **exTweather-hazard**: Sequential climate cascade analysis pipeline (flood → grid failure → heat → health impacts)

All packages are located in `Legacy code and supporting packages/`.

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

## Development Notes

### API Keys
All LLM-based tools (LLMeta, LLMscreen) require OpenAI API keys stored in `api.txt` files in their respective directories.

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
