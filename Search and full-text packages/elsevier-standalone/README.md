# Elsevier Standalone Downloader

A standalone Elsevier API PDF downloader (no dependency on the rest of this repository).

## 1) Install dependencies

```bash
cd /Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/elsevier-standalone
python3 -m pip install requests tqdm
```

## 2) Inputs

You must provide an API key (either option):

```bash
--api-key YOUR_KEY
```

or

```bash
export ELSEVIER_API_KEY=YOUR_KEY
```

If you have an institutional token, set it too:

```bash
export ELSEVIER_INST_TOKEN=YOUR_INSTTOKEN
```

DOIs can come from:
1. Multiple `--doi` arguments
2. A `--doi-file` in `csv/txt/json/jsonl`

## 3) Usage examples

Single DOI:

```bash
python3 downloader.py \
  --api-key YOUR_KEY \
  --inst-token YOUR_INSTTOKEN \
  --doi 10.1016/j.oneear.2026.101624 \
  --out-dir outputs_test
```

Wiley single DOI (new unified script):

```bash
python3 publisher_downloader.py \
  --publisher wiley \
  --wiley-token YOUR_WILEY_TDM_TOKEN \
  --doi 10.1002/asna.70088 \
  --out-dir wiley_test
```

Auto-detect publisher (Elsevier + Wiley mixed list):

```bash
python3 publisher_downloader.py \
  --publisher auto \
  --elsevier-api-key YOUR_ELSEVIER_KEY \
  --wiley-token YOUR_WILEY_TDM_TOKEN \
  --doi-file mixed_dois.csv \
  --doi-column doi \
  --title-column title \
  --out-dir mixed_test
```

Multiple DOIs (repeat argument):

```bash
python3 downloader.py \
  --api-key YOUR_KEY \
  --doi 10.1016/j.oneear.2026.101624 \
  --doi 10.1016/S0014-5793(01)03313-0
```

Read DOIs from one CSV column (default column name: `doi`):

```bash
python3 downloader.py \
  --api-key YOUR_KEY \
  --doi-file ./sample_dois.csv \
  --doi-column doi \
  --title-column title
```

Enable entitlement check (adds one extra API call per DOI):

```bash
python3 downloader.py \
  --api-key YOUR_KEY \
  --doi-file ./sample_dois.csv \
  --check-entitlement
```

Tune retry behavior for `429` / `5xx`:

```bash
python3 downloader.py \
  --api-key YOUR_KEY \
  --doi 10.1016/j.oneear.2026.101624 \
  --max-retries 4 \
  --backoff-seconds 1.0
```

## 4) Outputs

- `--out-dir/pdfs/*.pdf`
- `--out-dir/results.json`
- `--out-dir/results.csv`

Status values:
- `success`: Download succeeded and appears to be full PDF
- `success_limited`: Download succeeded but API returned first-page-limited PDF
- `exists`: PDF already exists locally
- `not_elsevier_doi`: DOI is not `10.1016/...`
- `missing_wiley_token`: Wiley download requested without token
- `unsupported_publisher`: DOI prefix not mapped to Elsevier or Wiley in auto mode

## 5) Security before sharing

- The script does **not** hardcode your API key.
- The script does **not** hardcode your institutional token.
- Prefer environment variable (`ELSEVIER_API_KEY`) instead of passing key in shell history.
- Prefer environment variable (`ELSEVIER_INST_TOKEN`) for insttoken.
- Keep insttoken server-side only (never in browser/client-side code).
- Never place insttoken in URL query params or address bars.
- Use HTTPS only for requests with insttoken.
- Before sending to your advisor, verify no key is in files:

```bash
rg -n "ELSEVIER_(API_KEY|INST_TOKEN)\\s*=\\s*['\\\"]|[0-9a-f]{32}" .
```

## 6) Insttoken troubleshooting

- If adding `--inst-token` causes `http_401`, check `X-ELS-Status` in response headers.
- A common cause is:
  - `AUTHENTICATION_ERROR - Institution Token is not associated with API Key`
- This means the insttoken and API key are not linked in the same Elsevier entitlement context.
- In that case, either:
  - request Elsevier to bind this token to your API key, or
  - use the API key alone (you may still get `success_limited` for non-entitled content).
