# Elsevier API Usage and Limits (Official References)

Last checked: 2026-03-18

## Core API docs

- API index: https://dev.elsevier.com/api_docs.html
- Article Retrieval API: https://dev.elsevier.com/documentation/ArticleRetrievalAPI.wadl
- API key settings (quotas/throttling): https://dev.elsevier.com/api_key_settings.html
- Support / quota increase requests: https://service.elsevier.com/app/contact/supporthub/researchproductsapis/

## Request format used by this standalone downloader

- Endpoint:
  - `https://api.elsevier.com/content/article/doi/{doi}`
- Required header:
  - `X-ELS-APIKey: <your_api_key>`
- Optional header:
  - `X-ELS-Insttoken: <institution_token>`
- For PDF:
  - `Accept: application/pdf`
- Alternative format parameter:
  - `httpAccept=application/pdf` (documented as override for `Accept`)

These are documented in the official Article Retrieval WADL.

## Institutional token (insttoken) terms from Elsevier Support

Elsevier Support additionally states these operational/security constraints for insttoken usage:

- Submit API key in header: `X-ELS-APIKey`
- Submit institution token in header: `X-ELS-Insttoken`
- All requests that include insttoken must use HTTPS.
- Keep insttoken server-side in a secure, password-protected environment.
- Do not expose insttoken in browser/client-side code.
- Do not expose insttoken in URL/address bar.
- insttoken may be revoked at any time without notice.
- insttoken represents full access under the linked customer entitlement context.

Important integration note from live API responses:

- `X-ELS-Insttoken` must be associated with the same `X-ELS-APIKey` account context.
- If they are not associated, API can return:
  - `HTTP 401`
  - `X-ELS-Status: AUTHENTICATION_ERROR - Institution Token is not associated with API Key`

## Official quota and throttling notes

From the API key settings page:

- Quotas reset every 7 days.
- Quotas are API-specific (not one global quota per key).
- Quota/usage headers:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset` (epoch seconds)
- `HTTP 429 TOO MANY REQUESTS` can happen for either:
  - quota exceeded (`X-ELS-Status: QUOTA_EXCEEDED - Quota Exceeded`)
  - requests-per-second throttling exceeded

## Article Retrieval limits shown on official table

The `api_key_settings.html` table lists for **Article Retrieval**:

- Weekly quota: `50,000` (or `Unlimited for Text Mining API Keys`)
- Requests per second: `10`
- Access scope: subscribed, open access, and complimentary articles

Important: limits can vary by key type and account setup. Treat values in the table as portal-configured defaults at the time of checking.

## Practical implications for this downloader

- If you get frequent `429`, slow down request rate and monitor `X-RateLimit-*` headers.
- If response is `200` with warning such as first-page-limited PDF, that is an entitlement/access-level issue, not transport failure.
- For higher quota or controlled API access, submit a request via Elsevier API Support.
