#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(shiny)
  library(httr)
  library(xml2)
})

API_BASE_URL <- "https://api.elsevier.com/content/article/doi/"
OUTPUT_ROOT <- normalizePath(file.path(getwd(), "shiny_outputs"), winslash = "/", mustWork = FALSE)
dir.create(OUTPUT_ROOT, recursive = TRUE, showWarnings = FALSE)
addResourcePath("figstore", OUTPUT_ROOT)

normalize_doi <- function(x) {
  d <- trimws(x)
  d <- sub("^https?://doi\\.org/", "", d, ignore.case = TRUE)
  d <- sub("^doi:\\s*", "", d, ignore.case = TRUE)
  tolower(trimws(d))
}

split_dois <- function(text) {
  raw <- unlist(strsplit(text, "[,\n\r\t; ]+"))
  raw <- raw[nzchar(trimws(raw))]
  dois <- unique(vapply(raw, normalize_doi, character(1)))
  dois[nzchar(dois)]
}

safe_name <- function(x) {
  gsub("[^A-Za-z0-9._-]+", "_", x)
}

build_headers <- function(api_key, inst_token) {
  h <- c(
    "Accept" = "text/xml",
    "X-ELS-APIKey" = api_key
  )
  if (nzchar(inst_token)) {
    h <- c(h, "X-ELS-Insttoken" = inst_token)
  }
  h
}

fetch_article_xml <- function(doi, api_key, inst_token) {
  url <- paste0(API_BASE_URL, URLencode(doi, reserved = TRUE))
  resp <- GET(
    url = url,
    add_headers(.headers = build_headers(api_key, inst_token)),
    query = list(httpAccept = "text/xml", view = "FULL"),
    timeout(90)
  )
  headers <- headers(resp)
  content_text <- content(resp, as = "text", encoding = "UTF-8")
  list(
    http_status = status_code(resp),
    api_status = headers[["x-els-status"]] %||% "",
    req_id = headers[["x-els-reqid"]] %||% "",
    content_type = headers[["content-type"]] %||% "",
    body = content_text
  )
}

`%||%` <- function(a, b) {
  if (is.null(a) || is.na(a)) b else a
}

extract_full_text <- function(xml_text) {
  doc <- read_xml(xml_text)
  p_nodes <- xml_find_all(
    doc,
    ".//*[local-name()='originalText']//*[local-name()='para' or local-name()='simple-para']"
  )
  p_text <- trimws(xml_text(p_nodes))
  p_text <- p_text[nzchar(p_text)]

  if (length(p_text) == 0) {
    fallback <- xml_find_all(doc, ".//*[local-name()='coredata']/*[local-name()='description']")
    p_text <- trimws(xml_text(fallback))
    p_text <- p_text[nzchar(p_text)]
  }

  paste(p_text, collapse = "\n\n")
}

extract_objects <- function(xml_text) {
  doc <- read_xml(xml_text)
  nodes <- xml_find_all(doc, ".//*[local-name()='object']")
  if (length(nodes) == 0) {
    return(data.frame(
      ref = character(0),
      category = character(0),
      type = character(0),
      mimetype = character(0),
      url = character(0),
      stringsAsFactors = FALSE
    ))
  }

  data.frame(
    ref = xml_attr(nodes, "ref"),
    category = xml_attr(nodes, "category"),
    type = xml_attr(nodes, "type"),
    mimetype = xml_attr(nodes, "mimetype"),
    url = trimws(xml_text(nodes)),
    stringsAsFactors = FALSE
  )
}

pick_figure_candidates <- function(objects, max_figures = 8) {
  if (nrow(objects) == 0) {
    return(objects)
  }
  mimetypes <- tolower(ifelse(is.na(objects$mimetype), "", objects$mimetype))
  objects <- objects[grepl("^image/", mimetypes), , drop = FALSE]
  if (nrow(objects) == 0) {
    return(objects)
  }

  rank_map <- c("standard" = 1, "high" = 2, "thumbnail" = 3)
  objects$cat_rank <- unname(rank_map[tolower(objects$category)])
  objects$cat_rank[is.na(objects$cat_rank)] <- 99
  objects <- objects[order(objects$ref, objects$cat_rank), , drop = FALSE]
  objects <- objects[!duplicated(objects$ref), , drop = FALSE]
  head(objects, max_figures)
}

ext_from_mimetype <- function(mimetype, url) {
  mt <- tolower(mimetype %||% "")
  if (mt == "image/jpeg") return("jpg")
  if (mt == "image/png") return("png")
  if (mt == "image/gif") return("gif")
  if (mt == "image/svg+xml") return("svg")
  if (grepl("\\.jpe?g($|\\?)", url, ignore.case = TRUE)) return("jpg")
  if (grepl("\\.png($|\\?)", url, ignore.case = TRUE)) return("png")
  if (grepl("\\.gif($|\\?)", url, ignore.case = TRUE)) return("gif")
  if (grepl("\\.svg($|\\?)", url, ignore.case = TRUE)) return("svg")
  "bin"
}

download_figures <- function(candidates, api_key, inst_token, doi_dir) {
  if (nrow(candidates) == 0) {
    return(data.frame(
      ref = character(0),
      category = character(0),
      mimetype = character(0),
      url = character(0),
      file_path = character(0),
      web_src = character(0),
      status = character(0),
      stringsAsFactors = FALSE
    ))
  }

  dir.create(doi_dir, recursive = TRUE, showWarnings = FALSE)
  out <- vector("list", nrow(candidates))
  headers <- build_headers(api_key, inst_token)

  for (i in seq_len(nrow(candidates))) {
    obj <- candidates[i, , drop = FALSE]
    ext <- ext_from_mimetype(obj$mimetype, obj$url)
    fname <- sprintf("%02d_%s_%s.%s", i, safe_name(obj$ref), safe_name(obj$category), ext)
    fpath <- file.path(doi_dir, fname)

    resp <- tryCatch(
      GET(obj$url, add_headers(.headers = headers), timeout(90)),
      error = function(e) e
    )

    if (inherits(resp, "error")) {
      out[[i]] <- data.frame(
        ref = obj$ref,
        category = obj$category,
        mimetype = obj$mimetype,
        url = obj$url,
        file_path = "",
        web_src = "",
        status = paste0("error:", conditionMessage(resp)),
        stringsAsFactors = FALSE
      )
      next
    }

    http_code <- status_code(resp)
    ctype <- headers(resp)[["content-type"]] %||% ""
    body_raw <- content(resp, as = "raw")

    if (http_code >= 400 || !grepl("^image/", tolower(ctype))) {
      out[[i]] <- data.frame(
        ref = obj$ref,
        category = obj$category,
        mimetype = obj$mimetype,
        url = obj$url,
        file_path = "",
        web_src = "",
        status = sprintf("http_%d_not_image", http_code),
        stringsAsFactors = FALSE
      )
      next
    }

    writeBin(body_raw, fpath)
    rel <- sub(paste0("^", gsub("([][{}()+*^$.|\\\\?])", "\\\\\\1", OUTPUT_ROOT), "/?"), "", fpath)
    rel <- gsub("\\\\", "/", rel)

    out[[i]] <- data.frame(
      ref = obj$ref,
      category = obj$category,
      mimetype = obj$mimetype,
      url = obj$url,
      file_path = fpath,
      web_src = paste0("figstore/", rel),
      status = "ok",
      stringsAsFactors = FALSE
    )
  }

  do.call(rbind, out)
}

ui <- fluidPage(
  tags$head(
    tags$style(HTML(
      "
      .fulltext-box {max-height: 360px; overflow-y: auto; background: #f7f7f7; border: 1px solid #ddd; padding: 10px;}
      .figure-grid {display: flex; flex-wrap: wrap; gap: 12px;}
      .figure-card {width: 220px; border: 1px solid #ddd; border-radius: 6px; padding: 8px; background: #fff;}
      .figure-card img {max-width: 100%; max-height: 140px; display: block; margin-bottom: 6px;}
      .doi-block {margin-top: 20px; padding-top: 8px; border-top: 1px solid #ddd;}
      "
    ))
  ),
  titlePanel("Elsevier Local Full-Text + Figures App"),
  sidebarLayout(
    sidebarPanel(
      width = 4,
      passwordInput("api_key", "Elsevier API Key"),
      passwordInput("inst_token", "Elsevier Institution Token (optional)"),
      textAreaInput(
        "doi_text",
        "DOI list (one DOI per line, or comma-separated)",
        value = "10.1016/j.ascom.2025.101023",
        rows = 8
      ),
      numericInput("max_figures", "Max figures per DOI", value = 8, min = 1, max = 50, step = 1),
      actionButton("fetch_btn", "Fetch Full Text + Figures", class = "btn-primary"),
      br(), br(),
      helpText("Security: keys/tokens are only used in-memory for requests and are not hardcoded.")
    ),
    mainPanel(
      width = 8,
      h4("Run Summary"),
      tableOutput("summary_tbl"),
      uiOutput("results_ui")
    )
  )
)

server <- function(input, output, session) {
  run_results <- reactiveVal(list())

  observeEvent(input$fetch_btn, {
    req(input$api_key)
    dois <- split_dois(input$doi_text)
    if (length(dois) == 0) {
      showNotification("Please provide at least one DOI.", type = "error")
      return(invisible(NULL))
    }

    run_id <- format(Sys.time(), "%Y%m%d_%H%M%S")
    out_root <- file.path(OUTPUT_ROOT, run_id)
    dir.create(out_root, recursive = TRUE, showWarnings = FALSE)

    results <- vector("list", length(dois))

    withProgress(message = "Fetching Elsevier content...", value = 0, {
      for (i in seq_along(dois)) {
        doi <- dois[[i]]
        incProgress(1 / length(dois), detail = doi)
        doi_dir <- file.path(out_root, safe_name(doi))

        one <- list(
          doi = doi,
          http_status = NA_integer_,
          api_status = "",
          req_id = "",
          full_text = "",
          full_text_chars = 0L,
          object_count = 0L,
          figure_count = 0L,
          figures = data.frame()
        )

        resp <- tryCatch(
          fetch_article_xml(doi, input$api_key, input$inst_token),
          error = function(e) list(http_status = NA_integer_, api_status = paste0("error:", conditionMessage(e)), req_id = "", body = "", content_type = "")
        )

        one$http_status <- resp$http_status %||% NA_integer_
        one$api_status <- resp$api_status %||% ""
        one$req_id <- resp$req_id %||% ""

        if (!is.na(one$http_status) && one$http_status == 200 && nzchar(resp$body %||% "")) {
          full_text <- tryCatch(extract_full_text(resp$body), error = function(e) "")
          objects <- tryCatch(extract_objects(resp$body), error = function(e) data.frame())
          candidates <- tryCatch(pick_figure_candidates(objects, input$max_figures), error = function(e) data.frame())
          figures <- tryCatch(download_figures(candidates, input$api_key, input$inst_token, doi_dir), error = function(e) data.frame())

          xml_path <- file.path(doi_dir, "article.xml")
          dir.create(doi_dir, recursive = TRUE, showWarnings = FALSE)
          writeLines(resp$body, xml_path, useBytes = TRUE)

          one$full_text <- full_text
          one$full_text_chars <- nchar(full_text)
          one$object_count <- nrow(objects)
          one$figure_count <- if (is.data.frame(figures)) sum(figures$status == "ok") else 0L
          one$figures <- figures
          one$xml_path <- xml_path
        }

        results[[i]] <- one
      }
    })

    run_results(results)
  })

  output$summary_tbl <- renderTable({
    res <- run_results()
    if (length(res) == 0) {
      return(data.frame())
    }
    data.frame(
      doi = vapply(res, `[[`, character(1), "doi"),
      http_status = vapply(res, function(x) as.character(x$http_status %||% ""), character(1)),
      api_status = vapply(res, `[[`, character(1), "api_status"),
      full_text_chars = vapply(res, `[[`, numeric(1), "full_text_chars"),
      objects = vapply(res, `[[`, numeric(1), "object_count"),
      figures_downloaded = vapply(res, `[[`, numeric(1), "figure_count"),
      stringsAsFactors = FALSE
    )
  }, striped = TRUE, bordered = TRUE, spacing = "s")

  output$results_ui <- renderUI({
    res <- run_results()
    if (length(res) == 0) {
      return(tags$p("Run the query to see full text and figures."))
    }

    blocks <- lapply(res, function(one) {
      fig_ui <- tags$p("No figures downloaded.")
      if (is.data.frame(one$figures) && nrow(one$figures) > 0) {
        ok <- one$figures[one$figures$status == "ok", , drop = FALSE]
        if (nrow(ok) > 0) {
          fig_cards <- lapply(seq_len(nrow(ok)), function(i) {
            f <- ok[i, , drop = FALSE]
            tags$div(
              class = "figure-card",
              tags$img(src = f$web_src),
              tags$div(tags$b(f$ref)),
              tags$div(sprintf("%s | %s", f$category, f$mimetype)),
              tags$a("Open", href = f$web_src, target = "_blank")
            )
          })
          fig_ui <- tags$div(class = "figure-grid", fig_cards)
        }
      }

      text_out <- if (nzchar(one$full_text)) one$full_text else "(No full text parsed)"
      tags$div(
        class = "doi-block",
        tags$h4(one$doi),
        tags$p(sprintf("HTTP: %s | API status: %s | ReqId: %s", one$http_status, one$api_status, one$req_id)),
        tags$p(sprintf("XML: %s", one$xml_path %||% "")),
        tags$details(
          tags$summary("Full Text (click to expand)"),
          tags$div(class = "fulltext-box", tags$pre(text_out))
        ),
        tags$h5("Figures"),
        fig_ui
      )
    })

    tags$div(blocks)
  })
}

shinyApp(ui = ui, server = server)
