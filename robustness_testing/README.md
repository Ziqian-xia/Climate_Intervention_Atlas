# Query Robustness Testing

This folder contains all files related to the robustness testing of the Auto-SLR query generation system.

## Purpose

Test the stability and sensitivity of the 4-agent query generation pipeline by:
- Generating 20 different query variations from the same research question
- Analyzing which terms cause high/low result counts
- Identifying systematic biases or instabilities in the LLM-based query generation

## Structure

```
robustness_testing/
├── README.md                          # This file
├── test_robustness_20runs.py          # Main test script (20 variations)
├── monitoring_scripts/                # Progress monitoring tools
│   ├── check_progress.sh              # Basic progress checker
│   ├── check_progress_new.sh          # Enhanced progress checker
│   └── watch_progress.sh              # Real-time file-based monitor
└── results/                           # All test results
    ├── 20260325_194108_complete/      # ⭐ MAIN RESULTS (Complete 20-variation test)
    │   ├── README.md                  # Quick start guide
    │   ├── ANALYSIS_SUMMARY_CN.md     # 📊 Detailed analysis (Chinese)
    │   ├── queries/                   # 20 generated query variations
    │   ├── search_results/            # Search results from OpenAlex
    │   └── analysis/                  # Sensitivity analysis outputs
    ├── 20260325_193211_interrupted/   # Interrupted test (3 databases)
    └── 3var_pilot_test/               # Initial 3-variation validation test
```

## Key Results

### Main Findings (20260325_194108_complete)

**Status**: ✅ Complete (20/20 variations, OpenAlex only)

**Key Statistics**:
- **Coefficient of Variation**: 378.6% (Very High - Indicates significant instability)
- **Result Range**: 9 - 87,884 papers
- **Ratio**: 9,765:1 (max/min)
- **Recommended Query**: Variation 1 (219 papers)

**Critical Issues Identified**:
1. **High instability** in LLM keyword expansion (CV = 378.6%)
2. **Variation 2 defect**: Retrieved 87,884 papers due to missing health/intervention constraints
3. **Expanding terms**: Generic methodology terms (e.g., "fixed effects", "event study") dramatically increase results
4. **Restricting terms**: Specific health terms (e.g., "heat warning system", "excess mortality") effectively narrow results

### Pilot Test (3var_pilot_test)

**Status**: ✅ Complete (3 variations, OpenAlex + PubMed)
**Purpose**: Validate testing infrastructure before full 20-variation run
**Results**: Confirmed variation exists, system works correctly

### Interrupted Test (20260325_193211_interrupted)

**Status**: ⚠️ Incomplete (stopped at Variation 6)
**Reason**: Configuration change needed (switch to OpenAlex-only)

---

## How to Use

### 1. View Main Results

Start here for complete analysis:
```bash
cd results/20260325_194108_complete
cat ANALYSIS_SUMMARY_CN.md  # Detailed Chinese analysis
cat README.md                # Quick overview
```

### 2. Run a New Test

```bash
# Basic test with default settings
python test_robustness_20runs.py --num-variations 20 --skip-confirmation

# Custom configuration
python test_robustness_20runs.py \
  --num-variations 10 \
  --databases openalex \
  --llm-provider bedrock \
  --max-results 999999 \
  --skip-confirmation
```

### 3. Monitor Running Test

```bash
# Option 1: Basic progress check
bash monitoring_scripts/check_progress.sh

# Option 2: Enhanced progress with statistics
bash monitoring_scripts/check_progress_new.sh

# Option 3: Real-time file monitoring
bash monitoring_scripts/watch_progress.sh
```

### 4. Access Generated Queries

```bash
# View a specific variation's query
cat results/20260325_194108_complete/queries/variation_01_queries.json | python -m json.tool

# Extract OpenAlex query for use
cat results/20260325_194108_complete/queries/variation_01_queries.json | \
  python -m json.tool | grep -A 1 '"openalex_query"'
```

### 5. Review Sensitivity Analysis

```bash
cd results/20260325_194108_complete/analysis/openalex

# View statistics
cat result_statistics.json

# View term impact rankings
head -50 impact_rankings.csv

# View correlations
cat correlations.csv
```

---

## Configuration

### Default Settings

- **Variations**: 20
- **Databases**: OpenAlex only (for efficiency)
- **Max Results**: Unlimited (download all matches)
- **Metadata**: DOI + OpenAlex ID only (minimal for speed)
- **LLM Provider**: AWS Bedrock (Claude Sonnet 4.6)

### Environment Variables Required

```bash
# AWS Bedrock
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export AWS_REGION="us-east-1"

# OpenAlex (optional but recommended)
export OPENALEX_API_KEY="your_key"
export OPENALEX_MAILTO="your_email"

# PubMed (if using pubmed database)
export PUBMED_API_KEY="your_key"
export PUBMED_EMAIL="your_email"

# Scopus (if using scopus database)
export ELSEVIER_API_KEY="your_key"
export ELSEVIER_INST_TOKEN="your_token"
```

---

## Next Steps

### Immediate Actions

1. **Use Variation 1** from the main results for Phase 2 (full-text retrieval)
2. **Review ANALYSIS_SUMMARY_CN.md** for detailed findings and recommendations
3. **Extract the query** and proceed to metadata search execution

### Medium-term Improvements

1. **Fix the prompt structure** to add mandatory concept constraints
2. **Enhance Sentinel Agent** to detect missing concept groups
3. **Re-run test** with improved prompt (target: CV < 50%)

### Alternative Approaches

1. **Ensemble strategy**: Combine 7 best variations (1, 4, 6, 9, 16, 18, 20)
2. **Hybrid approach**: Pre-define core terms + LLM expansion
3. **Manual refinement**: Use sensitivity analysis to hand-craft optimal query

---

## Files and Sizes

### Main Results Directory
- **Queries**: 20 JSON files (~20-30 KB each)
- **Search Results**: 20 directories with CSV/JSONL files
- **Analysis**: CSV files with term frequencies, correlations, rankings
- **Total Size**: ~150 MB (mostly DOI lists)

### Generated Papers
- **Total Retrieved**: 102,971 papers (including 87,884 from defective Variation 2)
- **Estimated Unique** (after removing Var 2): ~15,000 papers
- **Recommended Set** (Variation 1): 219 papers

---

## Related Files

- `/modules/m1_query_gen.py` - Query generation module (4-agent system)
- `/modules/m2_search_exec.py` - Search execution module
- `/modules/m5_sensitivity_analysis.py` - Sensitivity analysis module
- `/utils/cost_estimator.py` - Cost estimation utilities
- `/utils/query_parser.py` - Boolean query parser

---

## References

- Main repository documentation: `/CLAUDE.md`
- Previous variation analysis: `/QUERY_VARIATION_SUMMARY_FOR_ADVISOR.md`
- Plan file: `~/.claude/plans/logical-squishing-rain.md`

---

**Created**: 2026-03-25
**Last Updated**: 2026-03-25
**Status**: Active testing and analysis
