# Robustness Test Results - Complete Analysis

**Test Date**: March 25, 2026
**Configuration**: 20 query variations, OpenAlex only, full results download (DOI-only metadata)
**Status**: ✅ COMPLETED

---

## Quick Summary

- **Total Variations Generated**: 20/20 ✅
- **Total Searches Completed**: 20/20 ✅
- **Coefficient of Variation**: 378.6% ⚠️ (Very High - Indicates significant instability)
- **Result Range**: 9 - 87,884 papers (9,765:1 ratio)

---

## Key Files

### Analysis Results
- `ANALYSIS_SUMMARY_CN.md` - 完整中文分析报告（推荐首先阅读）
- `analysis/openalex/result_statistics.json` - 统计摘要
- `analysis/openalex/impact_rankings.csv` - 术语影响排名（完整版，400+ terms）
- `analysis/openalex/term_frequency.csv` - 术语频率矩阵
- `analysis/openalex/correlations.csv` - Query特征与结果数量的相关性

### Query Variations
- `queries/variation_01_queries.json` through `variation_20_queries.json` - 20个生成的queries

### Search Results
- `search_results/variation_XX/openalex/` - 每个variation的搜索结果
  - `run_summary.json` - 搜索统计（包含meta_count和results_count）
  - `works_summary.csv` - DOI列表
  - `works_full.jsonl` - 完整元数据（仅ID和DOI）

---

## Top Findings

### 1. Critical Issue: Variation 2 Query Defect

**Variation 2** retrieved 87,884 papers (97.5% of total) due to missing health/intervention constraints:
- Query only contains methodology terms (causal inference, quasi-experimental, etc.)
- **Missing**: heat warning, heat mortality, cooling center, temperature-health terms
- **Result**: Retrieved ALL causal inference papers across all disciplines

### 2. Best Performing Queries

**Recommended Primary Query**: **Variation 1** (219 papers)
- Well-balanced three-concept structure
- Includes: Interventions + Health Outcomes + Study Methods
- Reasonable recall without over-broadness

**Alternative Good Queries**:
- Variation 4 (511 papers)
- Variation 6 (189 papers)
- Variation 9 (218 papers)
- Variation 16 (280 papers)
- Variation 18 (312 papers)
- Variation 20 (145 papers)

### 3. Term Sensitivity Analysis

**EXPANDING terms** (avoid using alone):
- Methodology terms like "event study design", "fixed effects", "endogeneity"
- These are too generic without domain constraints
- Each adds ~87,000 papers when used alone

**RESTRICTING terms** (core terms - use these):
- "excess mortality" → -98.3% results (highly specific)
- "heat action plan" → -97.1% results
- "heat warning system" → -93.8% results
- "cooling center" → -93.5% results

---

## Recommendations

### Immediate Actions

1. **Use Variation 1 as your primary query** for the next phase
   - File: `queries/variation_01_queries.json`
   - Expected recall: ~219 papers from OpenAlex
   - Well-balanced and specific to your research question

2. **OR use an ensemble approach**:
   - Combine Variations: 1, 4, 6, 9, 16, 18, 20
   - Remove duplicates by DOI
   - Expected unique papers: ~1,200-1,500

3. **Extract Variation 1 query for Phase 2**:
   ```bash
   cat queries/variation_01_queries.json | python -m json.tool | grep -A 1 '"openalex_query"'
   ```

### Medium-term Improvements

1. **Fix the prompt structure**:
   - Add "MANDATORY CONCEPTS" section
   - Require each concept group (Intervention, Outcome, Method) to be present in EVERY query
   - See detailed suggestions in `ANALYSIS_SUMMARY_CN.md`

2. **Strengthen Sentinel Agent**:
   - Add checks for concept coverage
   - Flag queries missing any core concept group as CRITICAL ERROR
   - Force Refiner to add missing terms

3. **Re-run the test** with improved prompt:
   - Target CV < 50% (currently 378.6%)
   - Verify all 20 variations include health intervention terms

---

## Result Distribution

```
Variation         Count  Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Var  8                9  ❌ TOO NARROW
Var  7               59  ⚠️  TOO NARROW
Var 20              145  ✅ EXCELLENT
Var  6              189  ✅ EXCELLENT
Var  9              218  ✅ EXCELLENT
Var  1              219  ✅ EXCELLENT (Recommended)
Var 16              280  ✅ EXCELLENT
Var 18              312  ✅ EXCELLENT
Var 11              385  ✅ GOOD
Var 12              487  ✅ GOOD
Var  4              511  ✅ GOOD
Var 14              578  ✅ GOOD
Var  5              678  ✅ GOOD
Var 15            1,021  ✅ GOOD
Var 17            1,177  ✅ GOOD
Var 19            1,418  ✅ GOOD
Var 13            1,659  ⚠️  ACCEPTABLE
Var 10            2,475  ⚠️  ACCEPTABLE
Var  3            3,267  ⚠️  ACCEPTABLE
Var  2           87,884  ❌ CRITICAL (Query defect)
```

---

## Technical Details

### Test Configuration
- **Databases**: OpenAlex only (for efficiency)
- **Max Results**: Unlimited (downloaded all matches)
- **Metadata**: DOI + OpenAlex ID only (minimal data for speed)
- **LLM Provider**: AWS Bedrock (Claude Sonnet 4.6)
- **Execution Time**: ~50 minutes total
  - Phase 1 (Query Generation): ~25 minutes
  - Phase 2 (Search Execution): ~20 minutes
  - Phase 3 (Sensitivity Analysis): ~5 minutes

### Data Size
- **Queries**: 20 JSON files (~20-30 KB each)
- **Search Results**: 20 directories with run_summary.json + works CSV/JSONL
- **Total Papers Retrieved**: 102,971 (including the 87,884 from defective Variation 2)
- **Unique Papers** (estimated after removing Var 2): ~15,000

---

## Next Steps

### For Your Advisor Meeting

1. Show `ANALYSIS_SUMMARY_CN.md` - comprehensive Chinese summary
2. Highlight the instability issue (CV = 378.6%)
3. Explain the root cause (LLM keyword expansion inconsistency)
4. Present the solution (mandatory concept constraints + Sentinel enhancement)
5. Demonstrate that Variation 1 provides good balance (219 papers)

### For Phase 2 (Full Search Execution)

1. **Option A (Conservative)**: Use only Variation 1
   - Pros: High precision, manageable size
   - Cons: May miss some relevant papers

2. **Option B (Comprehensive)**: Use ensemble of 7 best variations
   - Variations: 1, 4, 6, 9, 16, 18, 20
   - Pros: Better recall, still reasonable size (~1,500 unique papers)
   - Cons: More papers to screen in Phase 3

3. **Then**: Proceed to full-text retrieval for selected papers
   - Use the fulltext-chain wrapper
   - Download PDFs/XMLs
   - Convert to Markdown for Phase 3 Claude screening

---

## Files Generated

```
robustness_test_results_20260325_194108/
├── README.md (this file)
├── ANALYSIS_SUMMARY_CN.md (详细中文报告)
├── queries/
│   └── variation_01_queries.json ... variation_20_queries.json
├── search_results/
│   └── variation_01/ ... variation_20/
│       └── openalex/
│           ├── run_summary.json
│           ├── works_summary.csv
│           └── works_full.jsonl
└── analysis/
    └── openalex/
        ├── result_statistics.json
        ├── term_frequency.csv
        ├── query_features.csv
        ├── correlations.csv
        └── impact_rankings.csv
```

---

**Test Completed**: 2026-03-25 20:28
**Total Execution Time**: ~50 minutes
**Status**: ✅ Success (with one defective query identified)
