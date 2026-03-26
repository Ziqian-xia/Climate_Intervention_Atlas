# Render RMarkdown Report to HTML
# This script renders the robustness analysis report

cat("========================================\n")
cat("Rendering Robustness Analysis Report\n")
cat("========================================\n\n")

# Check if rmarkdown is installed
if (!requireNamespace("rmarkdown", quietly = TRUE)) {
  cat("📦 Installing required packages...\n\n")
  install.packages("rmarkdown", repos = "https://cran.rstudio.com/")
}

# Check and install other required packages
required_packages <- c("ggplot2", "dplyr", "tidyr", "knitr", "kableExtra", "jsonlite", "gridExtra", "scales")

for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    cat(sprintf("📦 Installing %s...\n", pkg))
    install.packages(pkg, repos = "https://cran.rstudio.com/")
  }
}

cat("\n✅ All packages installed\n\n")

# Render the report
cat("📄 Rendering Robustness_Analysis_Report.Rmd...\n\n")

tryCatch({
  rmarkdown::render(
    input = "Robustness_Analysis_Report.Rmd",
    output_format = "html_document",
    output_file = "Robustness_Analysis_Report.html"
  )

  cat("\n========================================\n")
  cat("✅ Report rendered successfully!\n")
  cat("========================================\n\n")
  cat("📄 Output file: Robustness_Analysis_Report.html\n\n")
  cat("To view:\n")
  cat("  Open the HTML file in your browser\n")
  cat("  or run: browseURL('Robustness_Analysis_Report.html')\n\n")

}, error = function(e) {
  cat("\n❌ Rendering failed:\n")
  cat(as.character(e), "\n\n")
  cat("Troubleshooting:\n")
  cat("1. Make sure you're in the correct directory:\n")
  cat("   setwd('robustness_testing/results/latest')\n")
  cat("2. Make sure all data files exist:\n")
  cat("   - search_results/\n")
  cat("   - queries/\n")
  cat("   - analysis/openalex/\n")
  cat("3. Try rendering in RStudio:\n")
  cat("   Open the .Rmd file and click 'Knit' button\n\n")
})
