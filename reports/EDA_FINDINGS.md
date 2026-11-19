# MTA TransitPulse: exploratory findings, 2022–2025

## Decision summary

**Investigate F and Q first** as the two 2025 comparison groups that fall in both the worst six for customer journey-time performance and the highest six for net additional passenger minutes. F recorded **81.75% CJTP** and **232.0 million net additional passenger minutes**; Q recorded **79.84%** and **203.6 million**. B and D had the lowest CJTP (78.74% and 79.63%) and merit a separate reliability-focused review. This is a screening shortlist, not proof that a specific incident category caused delay or that one intervention will recover the measured minutes.

## Reliability and passenger impact

| 2025 service | CJTP | AJT, min/trip | Net passenger minutes | Weekday incidents | Weekday peak service delivered |
| --- | ---: | ---: | ---: | ---: | ---: |
| B | 78.74% | 2.57 | 173.5m | 2,087 | 91.11% |
| D | 79.63% | 2.04 | 148.1m | 2,774 | 93.39% |
| Q | 79.84% | 2.24 | 203.6m | 2,823 | 94.48% |
| F | 81.75% | 1.91 | 232.0m | 4,021 | 91.63% |

The 2025 customer source totals **3.241 billion net additional passenger minutes** across its measured weekday unlinked trips: 2.336 billion platform minutes and 0.905 billion onboard minutes. Waiting accounts for about **72.1%** of this net total. F is the largest single service burden; high-volume 1 and 6 also exceed 224 million minutes despite much higher CJTP (about 89%). Passenger burden and trip reliability should be read together.

Across all measured services, passenger-weighted CJTP rose from **83.88% in 2022** to **85.40% in 2025**, while AJT fell from **1.823 to 1.744 minutes per trip**. The 42nd Street Shuttle lacked two 2022 months; excluding it from both years gives a like-for-like CJTP change of **+1.43 percentage points** (83.82% to 85.25%). Net additional minutes still rose from **2.496 to 3.235 billion** for that matched service set as estimated passenger volume increased. An improvement per trip therefore did not mean a lower aggregate burden.

The weakest 2025 customer lines were B, D, Q, M, F and G. From 2022 to 2025, C improved by **5.69 percentage points**, A by **4.19**, and D by **3.47**; L fell by **2.06**, and G by **0.96**. These comparisons use complete 12-month years and passenger-weighted rates. In 2025, peak CJTP was **86.40%** versus **84.30%** off-peak; the peak/off-peak split is source-defined and covers weekdays only.

The four-year month-of-year check does not show a stable seasonal pattern. December averaged **0.55 percentage points below** its own year's CJTP, but this was driven mainly by December 2023 (1.94 points below that year's rate); December 2022 and 2025 were slightly above their annual rates. Treat month-of-year differences as exploratory.

## Operational patterns

In 2025, weekday delay-causing incidents were most often classified as **Police & Medical (16,215)** and **Infrastructure & Equipment (13,692)**, followed by Planned ROW Work (9,569). The largest raw weekday line counts were 6 (4,056), F (4,021), and the combined N/W group (3,640). These are event counts, not incident rates or severity measures. The MTA major-incident view is separate and cannot be added to them.

Across 1,101 line-months with incident records, the pooled Pearson correlation between weekday incident count and CJTP was **−0.486**. After removing average differences across lines and calendar months, the residual correlation was **−0.411**; the corresponding association with AJT was **+0.376**. All 23 line comparison groups had a negative within-line incident/CJTP correlation. The line-adjusted correlation between a month's incidents and the *next* month's CJTP was **−0.291**, weaker than the same-month pattern. These descriptive relationships do not establish cause or the effect of reducing a category of incidents.

Separate category-level adjusted correlations with CJTP were most negative for **Infrastructure & Equipment (−0.276)** and **Operating Conditions (−0.259)**. These categories occur in the same months and their attribution can change; the coefficients should guide case review, not be read as independent category effects or a causal ranking.

Weekday peak Service Delivered was **94.06%** in 2025 versus **92.91%** in 2022 for the comparable service set excluding the 42nd Street Shuttle, weighted by scheduled trains. F's 2025 rate was 91.63% and B's 91.11%, consistent with an operational delivery issue worth review alongside passenger metrics. The measure covers selected peak timepoints and cannot be treated as full-day customer reliability.

## Recommended next investigation

1. Review F and Q monthly performance and incident mix with operations staff, starting with months where CJTP and AJT deteriorated together.
2. Review B and D for persistent low CJTP, even though their total passenger-minute burdens rank below F and Q.
3. Keep 1 and 6 in a high-volume burden watchlist; their aggregate minutes are large despite better per-trip reliability.
4. Before a weighted priority score, compare rankings across years and plausible weights, confirm whether missing Major Incidents cells mean zero, and obtain a valid service-exposure denominator for incident rates.

The full [annual customer scorecard](../data/analysis/annual_customer_scorecard.csv) and [2025 comparison-group scorecard](../data/analysis/06_priority_analysis.csv) contain the reviewed figures. Reproducible queries are in [sql/analysis](../sql/analysis/), and [KPI_DEFINITIONS.md](KPI_DEFINITIONS.md) and [ANALYTICAL_LIMITATIONS.md](ANALYTICAL_LIMITATIONS.md) specify the metrics and caveats.
