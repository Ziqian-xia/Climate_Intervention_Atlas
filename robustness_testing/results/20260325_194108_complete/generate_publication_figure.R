#!/usr/bin/env Rscript
# Generate Publication-Quality Figure for Robustness Analysis
# This creates a comprehensive 3-panel figure showing:
# - Panel A: Result distribution across 20 variations
# - Panel B: Top expanding terms (increase results)
# - Panel C: Top restricting terms (decrease results)

cat("========================================\n")
cat("Generating Publication-Quality Figure\n")
cat("========================================\n\n")

# Load required libraries
required_packages <- c("ggplot2", "dplyr", "tidyr", "jsonlite", "gridExtra", "scales", "ggpubr")

for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    cat(sprintf("Installing %s...\n", pkg))
    install.packages(pkg, repos = "https://cran.rstudio.com/", quiet = TRUE)
  }
}

library(ggplot2)
library(dplyr)
library(jsonlite)
library(gridExtra)
library(scales)
library(ggpubr)

# Set working directory to script location
setwd("../../20260325_194108_complete")

cat("Loading data...\n")

# Load search results
results_list <- list()
for (var_dir in list.dirs("search_results", recursive = FALSE)) {
  var_num <- as.integer(sub(".*variation_(\\d+)", "\\1", basename(var_dir)))
  summary_file <- file.path(var_dir, "openalex", "run_summary.json")

  if (file.exists(summary_file)) {
    data <- fromJSON(summary_file)
    results_list[[length(results_list) + 1]] <- data.frame(
      variation = var_num,
      papers = data$meta_count
    )
  }
}

results_df <- bind_rows(results_list) %>% arrange(variation)

# Load term impact data
impact_df <- read.csv("analysis/openalex/impact_rankings.csv")
top_expanding <- impact_df %>% filter(impact_type == "EXPANDS") %>% arrange(desc(delta)) %>% head(8)
top_restricting <- impact_df %>% filter(impact_type == "RESTRICTS") %>% arrange(delta) %>% head(8)

cat("Creating visualizations...\n\n")

# Categorize results
results_df <- results_df %>%
  mutate(
    category = case_when(
      papers < 100 ~ "Too Narrow (<100)",
      papers <= 1500 ~ "Good (100-1,500)",
      papers <= 5000 ~ "Acceptable (1,500-5,000)",
      TRUE ~ "Too Broad (>5,000)"
    ),
    category = factor(category, levels = c("Too Narrow (<100)", "Good (100-1,500)",
                                            "Acceptable (1,500-5,000)", "Too Broad (>5,000)"))
  )

# Color palette
color_map <- c(
  "Too Narrow (<100)" = "#d62728",
  "Good (100-1,500)" = "#2ca02c",
  "Acceptable (1,500-5,000)" = "#ff7f0e",
  "Too Broad (>5,000)" = "#8b0000"
)

# ================ Panel A: Result Distribution ================
panel_a <- ggplot(results_df, aes(x = factor(variation), y = papers, fill = category)) +
  geom_bar(stat = "identity", color = "black", size = 0.8, alpha = 0.85) +
  geom_bar(data = filter(results_df, variation == 1),
           aes(x = factor(variation), y = papers),
           stat = "identity", fill = "#2ca02c", color = "#0066cc", size = 1.5) +
  geom_text(data = filter(results_df, papers > 10000 | variation %in% c(1, 8)),
            aes(label = format(papers, big.mark = ",")),
            vjust = -0.5, size = 3, fontface = "bold") +
  scale_fill_manual(values = color_map, name = "Quality Category") +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.1))) +
  labs(
    title = "A. Distribution of Retrieved Papers Across 20 Query Variations",
    x = "Query Variation Number",
    y = "Number of Papers Retrieved"
  ) +
  theme_minimal(base_size = 11) +
  theme(
    plot.title = element_text(size = 13, face = "bold", hjust = 0),
    axis.title = element_text(size = 12, face = "bold"),
    axis.text = element_text(size = 10),
    legend.position = "top",
    legend.title = element_text(face = "bold"),
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    plot.margin = margin(10, 10, 10, 10)
  ) +
  annotate("text", x = 18, y = max(results_df$papers) * 0.9,
           label = sprintf("CV = 378.6%%\nRange: 9 - 87,884\nMedian: 499"),
           hjust = 1, vjust = 1, size = 3.5, fontface = "bold",
           color = "black")

# ================ Panel B: Expanding Terms ================
panel_b <- top_expanding %>%
  mutate(term = reorder(term, delta)) %>%
  ggplot(aes(x = term, y = delta)) +
  geom_bar(stat = "identity", fill = "#d62728", color = "black",
           size = 0.8, alpha = 0.85) +
  geom_text(aes(label = sprintf("+%s\n(+%.0f%%)",
                                 format(delta, big.mark = ","),
                                 percent_change)),
            hjust = -0.1, size = 3, fontface = "bold") +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.15))) +
  coord_flip() +
  labs(
    title = "B. Top Terms That EXPAND Results",
    subtitle = "Generic methodology terms (must be combined with domain constraints)",
    x = NULL,
    y = "Increase in Papers"
  ) +
  theme_minimal(base_size = 11) +
  theme(
    plot.title = element_text(size = 13, face = "bold", hjust = 0),
    plot.subtitle = element_text(size = 9, face = "italic", hjust = 0, color = "#666666"),
    axis.title = element_text(size = 11, face = "bold"),
    axis.text = element_text(size = 10),
    panel.grid.major.y = element_blank(),
    panel.grid.minor = element_blank(),
    plot.margin = margin(10, 10, 10, 10)
  )

# ================ Panel C: Restricting Terms ================
panel_c <- top_restricting %>%
  mutate(term = reorder(term, abs(delta))) %>%
  ggplot(aes(x = term, y = abs(delta))) +
  geom_bar(stat = "identity", fill = "#2ca02c", color = "black",
           size = 0.8, alpha = 0.85) +
  geom_text(aes(label = sprintf("%s\n(%.1f%%)",
                                 format(delta, big.mark = ","),
                                 percent_change)),
            hjust = -0.1, size = 3, fontface = "bold") +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.15))) +
  coord_flip() +
  labs(
    title = "C. Top Terms That RESTRICT Results",
    subtitle = "Domain-specific terms (heat-health interventions)",
    x = NULL,
    y = "Decrease in Papers"
  ) +
  theme_minimal(base_size = 11) +
  theme(
    plot.title = element_text(size = 13, face = "bold", hjust = 0),
    plot.subtitle = element_text(size = 9, face = "italic", hjust = 0, color = "#666666"),
    axis.title = element_text(size = 11, face = "bold"),
    axis.text = element_text(size = 10),
    panel.grid.major.y = element_blank(),
    panel.grid.minor = element_blank(),
    plot.margin = margin(10, 10, 10, 10)
  )

# ================ Combine panels ================
cat("Combining panels...\n")

combined_plot <- ggarrange(
  panel_a,
  ggarrange(panel_b, panel_c, ncol = 2, labels = NULL),
  nrow = 2,
  heights = c(1.2, 1)
)

# Add overall title
final_plot <- annotate_figure(
  combined_plot,
  top = text_grob("Query Robustness Analysis: Result Distribution and Term Sensitivity",
                  face = "bold", size = 16)
)

# ================ Save figure ================
cat("Saving publication-quality figure...\n\n")

# PNG version (high resolution)
ggsave("Robustness_Analysis_Figure.png",
       plot = final_plot,
       width = 16, height = 14, units = "in",
       dpi = 300, bg = "white")

cat("✅ High-quality figure saved: Robustness_Analysis_Figure.png\n")
cat("   Resolution: 300 DPI (publication quality)\n")
cat("   Size: 16 × 14 inches\n\n")

# PDF version (vector graphics)
ggsave("Robustness_Analysis_Figure.pdf",
       plot = final_plot,
       width = 16, height = 14, units = "in",
       device = "pdf", bg = "white")

cat("✅ Vector version saved: Robustness_Analysis_Figure.pdf\n")
cat("   Format: PDF (scalable vector graphics)\n\n")

# ================ Create simplified key findings figure ================
cat("Creating key findings summary figure...\n\n")

# Variation comparison
var_comparison <- results_df %>% filter(variation %in% c(1, 2))

p_comparison <- ggplot(var_comparison,
                       aes(x = factor(variation, labels = c("Variation 1\n(Recommended)",
                                                             "Variation 2\n(Defective)")),
                           y = papers,
                           fill = factor(variation))) +
  geom_bar(stat = "identity", color = "black", size = 1.2, alpha = 0.85) +
  geom_text(aes(label = format(papers, big.mark = ",")),
            vjust = -0.5, size = 5, fontface = "bold") +
  scale_fill_manual(values = c("#2ca02c", "#d62728"), guide = "none") +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.1))) +
  labs(
    title = "The Critical Defect:\n401× Difference in Results",
    x = NULL,
    y = "Number of Papers"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
    axis.title.y = element_text(size = 12, face = "bold"),
    axis.text = element_text(size = 11),
    panel.grid.major.x = element_blank()
  ) +
  annotate("segment", x = 1, xend = 1, y = 219, yend = 15000,
           arrow = arrow(length = unit(0.3, "cm")), color = "darkgreen", size = 1) +
  annotate("text", x = 0.7, y = 20000,
           label = "Balanced query\nwith all concepts",
           hjust = 1, color = "darkgreen", fontface = "bold", size = 3.5) +
  annotate("segment", x = 2, xend = 2, y = 87884, yend = 60000,
           arrow = arrow(length = unit(0.3, "cm")), color = "darkred", size = 1) +
  annotate("text", x = 1.7, y = 55000,
           label = "Missing\nhealth terms",
           hjust = 0, color = "darkred", fontface = "bold", size = 3.5)

# Category distribution
cat_summary <- results_df %>%
  count(category) %>%
  mutate(percentage = n / sum(n) * 100)

p_distribution <- ggplot(cat_summary, aes(x = "", y = n, fill = category)) +
  geom_bar(stat = "identity", width = 1, color = "black", size = 1) +
  coord_polar("y") +
  scale_fill_manual(values = color_map) +
  geom_text(aes(label = sprintf("%d\n(%.0f%%)", n, percentage)),
            position = position_stack(vjust = 0.5),
            color = "white", fontface = "bold", size = 4) +
  labs(
    title = "Quality Distribution\nof 20 Query Variations",
    fill = "Category"
  ) +
  theme_void(base_size = 12) +
  theme(
    plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
    legend.position = "bottom",
    legend.title = element_text(face = "bold")
  )

# Combine key findings
key_findings <- ggarrange(p_comparison, p_distribution, ncol = 2, widths = c(1, 1))

ggsave("Key_Findings_Figure.png",
       plot = key_findings,
       width = 14, height = 6, units = "in",
       dpi = 300, bg = "white")

cat("✅ Key findings figure saved: Key_Findings_Figure.png\n\n")

# ================ Summary ================
cat("========================================\n")
cat("Publication-ready figures generated!\n")
cat("========================================\n\n")
cat("Files created:\n")
cat("1. Robustness_Analysis_Figure.png (comprehensive 3-panel)\n")
cat("2. Robustness_Analysis_Figure.pdf (vector format)\n")
cat("3. Key_Findings_Figure.png (summary)\n\n")
cat("Recommended usage:\n")
cat("- Use PNG files for presentations and reports\n")
cat("- Use PDF file for journal submissions (vector graphics)\n\n")
cat("All figures are publication-quality (300 DPI)\n")
