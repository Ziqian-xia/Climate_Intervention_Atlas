# Validation Notes (Existing Test Evidence)

Date consolidated: 2026-03-23

This project already contains archived run outputs showing successful full-text retrieval for each target channel.

Current strategy order in wrapper:
1. OpenAlex content API (OA-first)
2. Publisher APIs (Wiley, Elsevier)
3. Playwright fallback

## OA-first run verification

Run output:
- `/Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/fulltext-packages/validation_chain_oa_first_20260323`

Observed routing behavior:
- `10.1016/j.oneear.2026.101624`: OpenAlex `no_pdf_content_flag` -> falls back to Elsevier XML (`success_xml`)
- `10.1111/jofi.70001`: OpenAlex directly returned PDF (`success`), Wiley was not invoked
- `10.1038/s41591-023-02419-z`: OpenAlex PDF (`success`)

Summary:
- by_source: elsevier=1, openalex=2, wiley=0, playwright=0
- md_generated=3, md_success_strict=2

## New chain validation (XML/PDF/MD mode)

Executed with real tokens (no hardcoded credentials) using:
- `sample_dois.csv`
- output: `/Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/fulltext-packages/validation_chain_xml_pdf_md_final_20260323`

Observed:
- `10.1016/j.oneear.2026.101624` -> `elsevier` (`success_xml`, downloaded XML)
- `10.1111/jofi.70001` -> `wiley` (`success`)
- `10.1038/s41591-023-02419-z` -> `openalex` (`success`)

Summary:
- total = 3
- success = 3
- by_source: elsevier=1, wiley=1, openalex=1, playwright=0
- by_download_type: xml=1, pdf=2
- md_generated = 3
- md_success_strict = 2
- Per-item MD status:
  - Elsevier XML: `success`
  - Wiley PDF: `success_pypdf`
  - OpenAlex PDF: `placeholder_no_text:pdf_no_text_extracted` (placeholder md generated, OCR recommended)

## Elsevier API

Evidence file:
- `/Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/_intermediate_archive_20260323/check_non_oa_fulltext/results.csv`

Observed statuses:
- `success` (full PDF)
- `success_limited` (first-page-limited PDF from entitlement context)

Example rows:
- `10.1016/s0140-6736(15)60897-2` -> `success`
- `10.1016/j.envint.2018.08.049` -> `success`

## Wiley API

Evidence file:
- `/Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/_intermediate_archive_20260323/test_pub_wiley/results.csv`

Observed status:
- `success`

Example row:
- `10.1002/asna.70088` -> `success`

## OpenAlex Content API

Evidence files:
- `/Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/_intermediate_archive_20260323/content_from_step2_test_20260322/results.csv`
- `/Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/_intermediate_archive_20260323/content_wrapper_test_20260322/results.csv`

Observed statuses:
- `success` for PDF downloads on OA works
- `success` for `grobid_xml` when content exists
- expected non-success cases such as unresolved DOI / no content flag

Example rows:
- `W3171801815 (10.1038/s41558-021-01058-x)` -> `pdf success`
- `W3038568908 (10.1585/pfr.15.2402039)` -> `pdf success`, `grobid_xml success`

## Playwright fallback

Playwright is retained as last-resort fallback when API routes fail.  
It is intentionally not primary due to higher variability and browser dependencies.

Use:
- `--use-playwright-fallback`
- optional `--playwright-visible` for debugging

Bootstrap check in this environment:
- output: `/Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/fulltext-packages/validation_playwright_bootstrap_20260323`
- result: Playwright package import worked, but Chromium runtime was missing.
- action required: run `python3 -m playwright install chromium`
