# Full-Text Fetchers (Validated Chain)

This folder provides a validated full-text retrieval chain:

1. OpenAlex content API (OA-first)
2. Publisher APIs (Wiley, Elsevier)
3. Playwright browser fallback (only if 1-2 fail)

Script:
- `fulltext_chain_wrapper.py`

## Why this order

- OA-first reduces entitlement friction and cost on publisher APIs.
- Publisher APIs are second-line for licensed/non-OA retrieval.
- Playwright is last-resort browser automation and less deterministic.

## Install

```bash
cd /Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/fulltext-packages
python3 -m pip install -r requirements.txt
```

If you want Playwright fallback:

```bash
python3 -m playwright install chromium
```

If you want PDF->Markdown conversion via MinerU:

```bash
pip install "mineru[all]"
```

## Auth (no hardcoding)

```bash
export ELSEVIER_API_KEY="YOUR_ELSEVIER_KEY"
export ELSEVIER_INST_TOKEN="YOUR_ELSEVIER_INSTTOKEN_OPTIONAL"
export WILEY_TDM_CLIENT_TOKEN="YOUR_WILEY_TOKEN"
export OPENALEX_API_KEY="YOUR_OPENALEX_KEY"
export OPENALEX_MAILTO="your_email@domain.com"
```

## Run

```bash
python3 fulltext_chain_wrapper.py \
  --doi-file sample_dois.csv \
  --convert-to-md \
  --use-playwright-fallback \
  --out-dir run_fulltext_chain
```

Without browser fallback:

```bash
python3 fulltext_chain_wrapper.py \
  --doi-file sample_dois.csv \
  --out-dir run_fulltext_chain_no_browser
```

## Outputs

- `OUT_DIR/results.csv`
- `OUT_DIR/results.json`
- `OUT_DIR/run_summary.json`
- `OUT_DIR/downloads/elsevier/*.xml`
- `OUT_DIR/downloads/wiley/*.pdf`
- `OUT_DIR/downloads/openalex/*.pdf`
- `OUT_DIR/downloads/playwright/*.pdf`
- `OUT_DIR/md/...` (when `--convert-to-md` is enabled)

## Notes

- Elsevier requests include `view=FULL` and `httpAccept=text/xml`.
- Elsevier output status is `success_xml` / `success_limited_xml`.
- XML->Markdown is built in (`md_status=success` when conversion works).
- PDF->Markdown uses MinerU if available.
- If MinerU is unavailable, wrapper falls back to local PDF text extraction (`pypdf` / `PyMuPDF`) and writes markdown when possible.
- If a PDF has no extractable text, wrapper still writes a placeholder markdown with OCR hint (`md_status=placeholder_no_text:...`).
- Use `--accept-elsevier-limited-as-success` to stop immediately when limited XML is returned.
- Credentials are expected from env vars or CLI args only.

## Validation Snapshot

See:
- `VALIDATION_NOTES.md`
