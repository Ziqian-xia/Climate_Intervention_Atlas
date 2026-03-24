# Testing Guide for Search Wrappers

This document describes how to test the search functionality independently before using the UI.

## Prerequisites

Set up environment variables for the databases you want to test:

```bash
# OpenAlex (recommended, no key required)
export OPENALEX_MAILTO="your@email.com"
export OPENALEX_API_KEY="your_key"  # Optional, but recommended

# PubMed (free, no key required)
export PUBMED_EMAIL="your@email.com"
export PUBMED_API_KEY="your_ncbi_key"  # Optional, increases rate limit from 3 to 10 req/s

# Scopus (requires subscription/API key)
export SCOPUS_API_KEY="your_elsevier_key"
export SCOPUS_INST_TOKEN="your_institution_token"  # Optional
```

## Test Scripts

### 1. Individual Wrapper Tests

Test each database wrapper independently:

#### OpenAlex
```bash
python test_openalex.py
```

This tests:
- Full-text search (old method)
- Title+Abstract search (new method)
- Results parsing and display

#### PubMed
```bash
python test_pubmed.py
```

This tests:
- ESearch (finding PMIDs)
- EFetch (retrieving records)
- XML parsing
- Results display

#### Scopus
```bash
python test_scopus.py
```

This tests:
- Query execution
- Results parsing
- Error handling

### 2. Integrated SearchExecutor Test

Test the complete SearchExecutor module that integrates all wrappers:

```bash
python test_search_executor.py
```

This tests:
- Wrapper initialization
- Query execution
- Results saving to standardized format
- Output file structure (run_summary.json, works_summary.csv, works_full.jsonl)

## Expected Output Structure

Each database creates the following output structure:

```
<output_directory>/
├── <database>/
│   ├── run_summary.json      # Search metadata and stats
│   ├── works_summary.csv     # Flattened results (title, abstract, DOI, etc.)
│   └── works_full.jsonl      # Complete metadata (one JSON per line)
```

### Standard CSV Columns

**OpenAlex:**
- openalex_id, doi, title, abstract, publication_year, cited_by_count, is_oa

**PubMed:**
- pmid, doi, title, abstract, journal_title, publication_date

**Scopus:**
- eid, doi, title, abstract, creator, publication_name, cover_date, citedby_count

## Key Changes

### 1. OpenAlex: Title+Abstract Search
Changed from full-text search to title+abstract only:

**Before:**
```python
search_param="search"  # Searches all fields including full text
```

**After:**
```python
filter_str=f"title.search:{query}|abstract.search:{query}"  # Title OR Abstract only
```

### 2. PubMed: Fixed XML Parsing
Fixed `_parse_pubmed_xml` function import:

**Issue:** Was called as `self.wrapper._parse_pubmed_xml()` (doesn't exist as method)

**Fix:** Imported as standalone function and stored as `self._parse_pubmed_xml`

### 3. Scopus: Fixed Method Name
Fixed method name mismatch:

**Issue:** Called `self.wrapper.search_scopus()` (doesn't exist)

**Fix:** Changed to `self.wrapper.search_query()`

### 4. Scopus: Fixed Field Names
Updated field mappings for Scopus namespaced fields:

| Standard Field | Scopus Field Name |
|---------------|-------------------|
| doi | prism:doi |
| title | dc:title |
| abstract | dc:description |
| creator | dc:creator |
| publication_name | prism:publicationName |
| cover_date | prism:coverDate |

## Troubleshooting

### OpenAlex
- **No API key needed** for basic use, but recommended for politeness
- **Rate limits:** No hard limit, but be respectful
- **mailto parameter:** Helps OpenAlex contact you if needed

### PubMed
- **No API key needed** for basic use (3 req/s)
- **With API key:** 10 req/s rate limit
- **Email required:** Recommended by NCBI
- **Common errors:**
  - Query syntax: Use PubMed/Entrez format
  - Rate limiting: Add delay between requests

### Scopus
- **API key required:** Must have Elsevier/Scopus subscription
- **Institution token:** Optional, for institutional access
- **Rate limits:** Varies by subscription
- **Common errors:**
  - 401: Invalid API key
  - 403: No access to requested content
  - 429: Rate limit exceeded
  - Query syntax: Use Scopus format (TITLE-ABS-KEY)

## Next Steps

Once all tests pass:
1. Verify output files are created correctly
2. Check CSV data quality (no missing abstracts, DOIs, etc.)
3. Test with your actual research queries
4. Proceed to use the Streamlit UI with confidence

## Support

If tests fail:
1. Check error messages in console output
2. Verify environment variables are set correctly
3. Check API key permissions and quotas
4. Review logs in `logs/slr_pipeline.log`
