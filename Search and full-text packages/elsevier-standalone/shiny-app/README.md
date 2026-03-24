# Elsevier Local Shiny App

This local Shiny app lets you input:

- Elsevier API key
- Elsevier institution token (optional, but required for many entitlement contexts)
- One or more DOIs

And returns:

- Full-text XML content parsed into readable text
- Figure/object links parsed from XML
- Downloaded figure previews (image objects)

## 1) Install dependencies

```bash
cd /Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/elsevier-standalone/shiny-app
Rscript -e "install.packages(c('shiny','httr','xml2'), repos='https://cloud.r-project.org')"
```

## 2) Run locally

```bash
cd /Users/ziqianxia/Documents/GitHub/climate_evidence/literature-review/elsevier-standalone/shiny-app
Rscript -e "shiny::runApp('.', host='127.0.0.1', port=3838)"
```

Open: <http://127.0.0.1:3838>

## 3) Notes

- The app sends credentials only in request headers (`X-ELS-APIKey`, `X-ELS-Insttoken`).
- Keys/tokens are not hardcoded in source.
- Downloaded outputs are saved under:
  - `shiny_outputs/<timestamp>/<doi_safe_name>/`
