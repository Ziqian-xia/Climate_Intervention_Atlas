# Full-Text Retrieval Guide

## Overview

Phase 4 of the Auto-SLR pipeline retrieves full-text PDFs and XML files from multiple sources using a waterfall strategy:

1. **OpenAlex Content API** (OA-first, free PDFs)
2. **Publisher APIs** (Elsevier XML, Wiley PDF)
3. **Playwright Browser Fallback** (optional, last resort)

## Supported Publishers

### Wiley (NEW)

**Coverage:** 10.1002/*, 10.1111/*

**API:** Wiley TDM (Text and Data Mining) Client Token

**How to get access:**
1. Visit: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining
2. Apply for TDM access through your institutional library
3. Receive a UUID token (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
4. Add to `.env`: `WILEY_TDM_CLIENT_TOKEN=your_token_here`

**What you get:**
- Full-text PDFs
- No page limits
- Direct API access (no browser automation needed)

**Test results:**
```
✅ 10.1002/joc.5086 - Successfully downloaded (22.77 MB)
✅ 10.1111/gcb.13456 - Successfully downloaded (1.03 MB)
```

### Elsevier

**Coverage:** 10.1016/*

**API:** Elsevier Article Retrieval API

**How to get access:**
1. Visit: https://dev.elsevier.com/
2. Register for API key
3. Optionally: Get institutional token for full access
4. Add to `.env`:
   ```
   ELSEVIER_API_KEY=your_api_key
   ELSEVIER_INST_TOKEN=your_inst_token  # optional
   ```

**What you get:**
- Full-text XML (structured content)
- Without inst token: First page only
- With inst token: Full article

### OpenAlex

**Coverage:** Open Access papers from all publishers

**API:** OpenAlex Content API ($0.01 per PDF)

**How to get access:**
1. Visit: https://openalex.org/
2. Sign up for API key (optional but recommended)
3. Add to `.env`:
   ```
   OPENALEX_API_KEY=your_key
   OPENALEX_MAILTO=your_email@domain.com
   ```

**What you get:**
- Free/OA PDFs from institutional repositories
- Preprints and postprints
- Often lower quality than publisher versions

## Retrieval Strategy

The system tries sources in this order:

```
1. OpenAlex (OA-first strategy)
   ├─ Success? → Done
   └─ Failed → Try publisher API

2. Publisher API (Wiley or Elsevier based on DOI)
   ├─ Success? → Done
   └─ Failed → Try Playwright fallback (if enabled)

3. Playwright Browser Automation (optional)
   ├─ Success? → Done
   └─ Failed → Mark as failed
```

## Configuration in App

**Phase 4 Settings:**

- **Use Playwright Fallback:** Enable browser automation for paywalled content
  - Slower and less reliable
  - Useful for papers not available via APIs
  - Requires `playwright` package and Chromium

- **Max Retries:** Number of retry attempts for failed API calls (1-10)
  - Default: 3
  - Higher values help with transient failures

- **Timeout:** Request timeout in seconds (30-300)
  - Default: 60s
  - Increase for large files or slow connections

## Output Structure

```
fulltext_YYYYMMDD_HHMMSS/
├── downloads/
│   ├── elsevier/        # XML files from Elsevier
│   ├── wiley/           # PDFs from Wiley
│   ├── openalex/        # PDFs from OpenAlex
│   └── playwright/      # PDFs from browser fallback
├── md/                  # Converted markdown (if enabled)
│   ├── elsevier/
│   ├── wiley/
│   ├── openalex/
│   └── playwright/
├── results.csv          # Per-DOI retrieval status
├── results.json         # Full results with metadata
└── run_summary.json     # Aggregated statistics
```

## Results CSV Columns

- `doi`: Document DOI
- `title`: Paper title
- `journal`: Journal name
- `success`: Boolean - retrieval succeeded
- `final_source`: Source that succeeded (openalex/wiley/elsevier/playwright)
- `final_status`: Detailed status code
- `download_path`: Path to downloaded file
- `download_type`: File format (pdf/xml)
- `file_bytes`: File size in bytes
- `elsevier_status`: Elsevier attempt status
- `wiley_status`: Wiley attempt status
- `openalex_status`: OpenAlex attempt status
- `playwright_status`: Playwright attempt status
- `md_path`: Converted markdown path (if conversion enabled)
- `md_status`: Markdown conversion status
- `note`: Additional details or warnings

## Testing the Integration

Run the test script:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run test
python3 test_wiley_fulltext.py
```

**Expected output:**
```
Testing Wiley Full-Text Retrieval
==================================
Environment Check: ✅ All credentials set
Testing 3 DOIs...
✅ Wiley API: 2 papers downloaded
Total: 3 | Success: 2 | Failed: 1
```

## Troubleshooting

### Wiley API Errors

**HTTP 401 - Unauthorized:**
- Check token format (should be UUID)
- Verify institutional access
- Contact library for token renewal

**HTTP 403 - Forbidden:**
- DOI not covered by your subscription
- Check if journal is in Wiley's TDM program

**HTTP 404 - Not Found:**
- Invalid DOI
- Paper not available in Wiley collection

### Elsevier API Errors

**HTTP 401 - Invalid API Key:**
- Verify API key is correct
- Check key hasn't expired
- Re-generate key from dev.elsevier.com

**Limited to first page:**
- Add institutional token to `.env`
- Contact Elsevier for entitlement verification

### OpenAlex API Errors

**doi_unresolved:**
- DOI not indexed in OpenAlex
- Try publisher APIs instead

**no_pdf_content_flag:**
- Paper not open access
- No full-text available via OpenAlex

## Cost Estimation

**Per 1000 Papers:**

| Source | API Calls | Cost | Success Rate |
|--------|-----------|------|--------------|
| OpenAlex Content | 1000 | $10 | 30-50% (OA papers) |
| Wiley TDM | 300-500 | Free* | 90-95% (Wiley papers) |
| Elsevier | 200-400 | Free* | 80-90% (Elsevier papers) |
| Playwright | 100-300 | Free (self-hosted) | 50-70% |

*Free with institutional subscription

**Estimated total:** $10-15 per 1000 papers (OpenAlex only)

**Recommended strategy:**
- Use OA-first (OpenAlex) to minimize publisher API calls
- Publisher APIs for closed-access papers
- Disable Playwright to save time unless needed

## Integration Status

✅ **Wiley TDM API** - Fully tested and working (2024-03-24)
- Token format: UUID
- Downloads full-text PDFs
- No page limits

⚠️ **Elsevier API** - Configured but needs valid credentials
- Requires API key and optional institutional token

✅ **OpenAlex API** - Configured and ready
- Optional API key improves rate limits

✅ **Phase 4 UI** - Fully integrated in Auto-SLR app
- Configuration panel
- Progress tracking
- Results visualization

## Next Steps

1. **Add your credentials** to `.env` file
2. **Run Phase 3** screening to get approved papers
3. **Configure Phase 4** settings in the app
4. **Start retrieval** and monitor progress
5. **Review results** in the output directory

## References

- Wiley TDM: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining
- Elsevier API: https://dev.elsevier.com/
- OpenAlex: https://docs.openalex.org/
