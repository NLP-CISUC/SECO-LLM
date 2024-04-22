lines <- readLines("results/evaluation/evaluation_2024_04_16_15_55_49.jsonl")
lines <- lapply(lines, jsonlite::fromJSON)
lines <- lapply(lines, unlist)
df <- dplyr::bind_rows(lines)
df$score <- as.numeric(df$score)

insufficient <- names(which(table(df$uuid) < 10))
df <- df[!df$uuid %in% insufficient, ]

agg_df <- aggregate(x = as.numeric(df$score),
                    by = list(df$joke_id),
                    FUN = mean)
colnames(agg_df)[1] <- "joke_id"
colnames(agg_df)[2] <- "score"

# Test Normality
shapiro.test(agg_df$score)
cat("\n******************************\n\n")

# Test if mean location is 0
wilcox.test(agg_df$score, mu = 0,
            alternative = "two.sided",
            conf.int = TRUE,
            conf.level = 0.95)
cat("\n******************************\n\n")

# Check agreement with Krippendorff's Alpha
pivot_scores <- tidyr::pivot_wider(df, id_cols = uuid,
                                   names_from = joke_id,
                                   values_from = score)
pivot_scores <- as.matrix(dplyr::select(pivot_scores, -uuid))
irr::kripp.alpha(pivot_scores, method = "interval")
cat("\n******************************\n\n")

# Two-way ANOVA to check if evaluator distributions differ
two.way <- aov(df$score ~ as.factor(df$uuid) + as.factor(df$joke_id))
summary(two.way)

