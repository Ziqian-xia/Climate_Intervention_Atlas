# Search Wrapper Test Results

**Date**: 2026-03-23
**Status**: ✅ **ALL TESTS PASSED**

## Test Summary

All three database search wrappers have been tested and are working correctly:

| Database | Status | Results | Time |
|----------|--------|---------|------|
| OpenAlex | ✅ Success | 10/10 | <1s |
| PubMed | ✅ Success | 10/10 | 1s |
| Scopus | ✅ Success | 10/10 | 7s |

## Test Configuration

**Test Query:**
- **OpenAlex**: "climate change health impacts" (plain text)
- **PubMed**: `("climate change"[Title/Abstract] AND "health"[Title/Abstract])`
- **Scopus**: `TITLE-ABS-KEY("climate change" AND "health")`

**API Keys Used:**
- ✅ OpenAlex API Key: Configured
- ✅ PubMed API Key: Configured (10 req/s rate limit)
- ✅ Scopus API Key: Configured

## Detailed Results

### 1. OpenAlex

**Query Type**: Title + Abstract search
**Implementation**: Uses `search` parameter (searches title, abstract, and entity names - NOT full-text)
**Total Found**: 1,273,305 matching papers
**Retrieved**: 10 papers

**Sample Result:**
- **Title**: Impact of regional climate change on human health
- **DOI**: https://doi.org/10.1038/nature04188
- **Year**: 2005
- **Citations**: 3,046
- **Open Access**: No

**Output Files:**
- ✅ `run_summary.json` (157 bytes)
- ✅ `works_summary.csv` (10 records)
- ✅ `works_full.jsonl` (10 records)

### 2. PubMed

**Query Type**: ESearch + EFetch (Title/Abstract fields)
**Total Found**: 17,820 matching papers
**Retrieved**: 10 papers
**Rate Limit**: 10 requests/second (with API key)

**Sample Result:**
- **PMID**: 41871847
- **DOI**: 10.1136/bmjgh-2024-017222
- **Title**: Climate reparations for threats to health
- **Journal**: BMJ Global Health
- **Date**: 2026-03-23
- **Abstract**: Climate change is already leading to loss of health... (full abstract available)

**Output Files:**
- ✅ `run_summary.json` (177 bytes)
- ✅ `works_summary.csv` (14,745 bytes - includes full abstracts)
- ✅ `works_full.jsonl` (26,262 bytes)

### 3. Scopus

**Query Type**: TITLE-ABS-KEY search
**Total Found**: Unknown (Scopus doesn't return total count reliably)
**Retrieved**: 10 papers
**API Performance**: ~7 seconds for 10 results

**Sample Result:**
- **EID**: 2-s2.0-105030863542
- **DOI**: 10.1038/s44401-025-00057-w
- **Title**: Using data science to identify climate change and health adverse impacts and solutions in Africa: a scoping review
- **Author**: Wright C.Y.
- **Publication**: Npj Health Systems
- **Date**: 2026-12-01
- **Citations**: 0 (very recent)

**Output Files:**
- ✅ `run_summary.json` (206 bytes)
- ✅ `works_summary.csv` (2,095 bytes)
- ✅ `works_full.jsonl` (17,513 bytes)

## Fixed Issues

### 1. OpenAlex Filter Syntax Error ✅ Fixed
**Problem**: Attempted to use OR filter between different fields:
`title.search:X|abstract.search:Y` → ❌ Not supported by OpenAlex

**Solution**: Use default `search` parameter which already searches title + abstract (not full-text)

**Result**: ✅ Now working correctly

### 2. PubMed XML Parsing ✅ Fixed
**Problem**: `_parse_pubmed_xml` was called as instance method but is a standalone function

**Solution**: Import function separately and store as `self._parse_pubmed_xml`

**Result**: ✅ XML parsing now works

### 3. Scopus Method Name ✅ Fixed
**Problem**: Called `search_scopus()` but method is named `search_query()`

**Solution**: Updated method call to `search_query()`

**Result**: ✅ Scopus search now works

### 4. Scopus Field Mapping ✅ Fixed
**Problem**: Scopus uses namespaced fields (`dc:`, `prism:`) but code expected flat names

**Solution**: Updated field mappings:
- `doi` → `prism:doi`
- `title` → `dc:title`
- `abstract` → `dc:description`
- etc.

**Result**: ✅ Correct data extraction

## Key Insights

### OpenAlex Search Behavior
The `search` parameter in OpenAlex:
- ✅ **Searches**: Title, abstract, entity names (authors, institutions)
- ❌ **Does NOT search**: Full-text content
- **Source**: [OpenAlex API Documentation](https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/search-entities)

This means OpenAlex is already doing title+abstract search by default - no special filtering needed!

### Database Comparison

| Feature | OpenAlex | PubMed | Scopus |
|---------|----------|--------|--------|
| **Coverage** | ~250M works | ~37M citations | ~90M+ abstracts |
| **API Cost** | Free | Free | Paid (subscription) |
| **Rate Limit** | Polite | 3-10 req/s | Varies |
| **Abstract Quality** | Variable | Excellent | Excellent |
| **Full-Text** | Links only | Links only | Links only |
| **Speed** | Fast (<1s) | Fast (1-2s) | Slower (5-10s) |

## Recommendations

1. **Use all three databases** for comprehensive coverage
2. **OpenAlex** should be primary source (free, fast, large coverage)
3. **PubMed** for biomedical/health focus
4. **Scopus** for broader academic coverage (if API access available)
5. **Deduplicate by DOI** after merging results (Phase 3 handles this)

## Next Steps

✅ All internal testing complete
✅ Ready for UI testing in Phase 2
✅ Streamlit app restarted with fixed code at http://localhost:8501

You can now:
1. Go to Phase 2 in the UI
2. Configure API keys (already set via environment variables)
3. Run searches on OpenAlex, PubMed, and Scopus
4. Verify results are saved correctly
5. Proceed to Phase 3 (Abstract Screening with Claude)
