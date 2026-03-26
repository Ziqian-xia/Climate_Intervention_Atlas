# Generate Publication-Quality Figure
cat("Generating publication-quality figure...\n\n")

# Load required libraries
suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(jsonlite)
  library(gridExtra)
  library(scales)
  library(ggpubr)
})

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

# Load term impact
impact_df <- read.csv("analysis/openalex/impact_rankings.csv")
top_expanding <- impact_df %>% filter(impact_type == "EXPANDS") %>% arrange(desc(delta)) %>% head(8)
top_restricting <- impact_df %>% filter(impact_type == "RESTRICTS") %>% arrange(delta) %>% head(8)

# Categorize
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

color_map <- c(
  "Too Narrow (<100)" = "#d62728",
  "Good (100-1,500)" = "#2ca02c",
  "Acceptable (1,500-5,000)" = "#ff7f0e",
  "Too Broad (>5,000)" = "#8b0000"
)

# Panel A
panel_a <- ggplot(results_df, aes(x = factor(variation), y = papers, fill = category)) +
  geom_bar(stat = "identity", color = "black", size = 0.8, alpha = 0.85) +
  geom_bar(data = filter(results_df, variation == 1),
           stat = "identity", fill = "#2ca02c", color = "#0066cc", size = 1.5) +
  geom_text(data = filter(results_df, papers > 10000 | variation %in% c(1, 8)),
            aes(label = format(papers, big.mark = ",")),
            vjust = -0.5, size = 3, fontface = "bold") +
  scale_fill_manual(values = color_map, name = "Quality Category") +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.1))) +
  labs(title = "A. Distribution of Retrieved Papers Across 20 Query Variations",
       x = "Query Variation Number", y = "Number of Papers Retrieved") +
  theme_minimal(base_size = 11) +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0),
        axis.title = element_text(size = 12, face = "bold"),
        legend.position = "top", panel.grid.major.x = element_blank()) +
  annotate("text", x = 18, y = max(results_df$papers) * 0.9,
           label = "CV = 378.6%\nRange: 9 - 87,884\nMedian: 499",
           hjust = 1, size = 3.5, fontface = "bold")

# Panel B
panel_b <- top_expanding %>%
  mutate(term = reorder(term, delta)) %>%
  ggplot(aes(x = term, y = delta)) +
  geom_bar(stat = "identity", fill = "#d62728", color = "black", size = 0.8, alpha = 0.85) +
  geom_text(aes(label = sprintf("+%s", format(delta, big.mark = ","))),
            hjust = -0.1, size = 3, fontface = "bold") +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.15))) +
  coord_flip() +
  labs(title = "B. Top Terms That EXPAND Results",
       subtitle = "Generic methodology terms", x = NULL, y = "Increase in Papers") +
  theme_minimal(base_size = 11) +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0),
        plot.subtitle = element_text(size = 9, face = "italic", color = "#666666"),
        panel.grid.major.y = element_blank())

# Panel C
panel_c <- top_restricting %>%
  mutate(term = reorder(term, abs(delta))) %>%
  ggplot(aes(x = term, y = abs(delta))) +
  geom_bar(stat = "identity", fill = "#2ca02c", color = "black", size = 0.8, alpha = 0.85) +
  geom_text(aes(label = format(delta, big.mark = ",")),
            hjust = -0.1, size = 3, fontface = "bold") +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.15))) +
  coord_flip() +
  labs(title = "C. Top Terms That RESTRICT Results",
       subtitle = "Domain-specific terms", x = NULL, y = "Decrease in Papers") +
  theme_minimal(base_size = 11) +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0),
        plot.subtitle = element_text(size = 9, face = "italic", color = "#666666"),
        panel.grid.major.y = element_blank())

# Combine
combined <- ggarrange(
  panel_a,
  ggarrange(panel_b, panel_c, ncol = 2),
  nrow = 2, heights = c(1.2, 1)
)

final_plot <- annotate_figure(
  combined,
  top = text_grob("Query Robustness Analysis: Result Distribution and Term Sensitivity",
                  face = "bold", size = 16)
)

# Save
ggsave("Robustness_Analysis_Figure.png", plot = final_plot,
       width = 16, height = 14, dpi = 300, bg = "white")

ggsave("Robustness_Analysis_Figure.pdf", plot = final_plot,
       width = 16, height = 14, device = "pdf", bg = "white")

cat("\n✅ Figures saved successfully!\n")
cat("   - Robustness_Analysis_Figure.png (300 DPI, 16×14 inches)\n")
cat("   - Robustness_Analysis_Figure.pdf (vector graphics)\n\n")
cat("Location: robustness_testing/results/20260325_194108_complete/\n")
