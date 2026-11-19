# MTA TransitPulse | Subway Reliability and Passenger Impact

**Executive case study · Data Analyst portfolio project · Prepared 19 November 2026**
**Evidence period:** January 2022–December 2025 · **Source snapshot:** 19 November 2026

## Executive summary

Passenger-weighted weekday Customer Journey Time Performance (CJTP) improved from **83.88% in 2022 to 85.40% in 2025**, a gain of **1.52 percentage points** across the published customer observations. The 42nd Street Shuttle lacks two 2022 months; excluding it from both years gives a more comparable **+1.43-point** gain. These are measured changes, not evidence that a particular intervention caused the improvement. [1, 5]

The 2025 customer data still imply **3.24 billion net additional passenger minutes** across the measured weekday unlinked trips. This is a signed model estimate within the MTA metric's coverage, not all subway riders' lost time. A lower average additional journey time per trip coexisted with a larger aggregate time burden as estimated trip volume grew. [1, 5]

For the next diagnostic cycle, investigate **F, B, and Q** first under a proposed 2025 score combining reliability, passenger burden, and peak service delivery. Their baseline ranks are 1, 2, and 3; each remains in the top four across five weight scenarios. Review **D** separately for persistent weak reliability despite a below-median passenger-time burden. These ranks screen investigations; they do not estimate benefits or prescribe service changes. [3, 6]

## Business problem and decision

Systemwide averages can improve while particular lines continue to expose many passengers to unreliable or longer trips. An operations team needs a consistent way to identify where customer impact is large, distinguish per-trip reliability from aggregate burden, and decide which line-level issues deserve more detailed review. TransitPulse links customer estimates to incident and service-delivery summaries at a common monthly comparison-group grain, then presents the evidence in a four-page Power BI report. [1–4, 5]

## Data and method

The project uses four MTA Open Data sources: Customer Journey-Focused Metrics, Delay-Causing Incidents, Major Incidents, and Service Delivered. The downloaded snapshot covers 48 months from January 2022 through December 2025. Python validates and standardizes the raw files; PostgreSQL stores four fact tables and reporting views; SQL and Python produce analyses and a fixed 2025 priority scorecard; Power BI imports validated reporting snapshots. The 21,475 raw rows reconcile to 21,475 processed fact rows, and the reporting layer passes ten additional checks. [1–4, 7]

CJTP is `100 × (1 − sum(trips over five additional minutes) / sum(estimated passenger trips))`. Additional Journey Time (AJT) is net additional platform plus train minutes divided by passenger trips. Calculations pool numerators and denominators before computing a rate; they do not average monthly percentages. Customer estimates cover weekday unlinked train trips from 6 a.m. to 11 p.m. The incident source covers all weekday hours, and Service Delivered covers selected peak timepoints. [1, 5]

For cross-source analysis, N and W are combined as `NW` because the incident sources publish them together. The 42nd Street Shuttle's January–February 2022 customer observations are absent. Missing incident records remain missing rather than being read as zero. [5, 7]

## Findings that change the investigation order

### Reliability improved, but the passenger-time burden grew

Across the measured customer population, CJTP rose **1.52 points** from 2022 to 2025. AJT fell from **1.823 to 1.744 net minutes per trip**. On a matched set excluding the 42nd Street Shuttle, CJTP rose **1.43 points**, while total net additional time increased from **2.496B to 3.235B minutes** as estimated passenger volume increased. The aggregate total is therefore a volume-sensitive measure, not a direct test of whether each trip became worse. [5]

In 2025, **2.336B** net additional minutes were attributed to platforms and **0.905B** to trains. Platform time represented about **72.1%** of the net total. These signed components can offset one another; the total should not be described as the sum of positive delays for individual riders. [5]

![Executive Overview dashboard](../dashboards/screenshots/Executive%20Overview.png)

### F, B, and Q are robust first investigations

| Line group | 2025 CJTP | Net additional minutes | Peak Service Delivered | Baseline rank | Rank range across five scenarios |
| --- | ---: | ---: | ---: | ---: | ---: |
| F | 81.75% | 232.0M | 91.63% | 1 | 1–2 |
| B | 78.74% | 173.5M | 91.11% | 2 | 1–3 |
| Q | 79.84% | 203.6M | 94.48% | 3 | 2–4 |
| D | 79.63% | 148.1M | 93.39% | 5 | 4–10 |

F has the largest 2025 net passenger-time burden among the 23 comparison groups. B has the lowest CJTP and highest AJT. Q combines weak CJTP with more than 200M net minutes. The proposed baseline score weights poor reliability at 40%, passenger burden at 40%, and low peak service delivery at 20%. F/B/Q remain the first-review set across plausible weight alternatives. D has the second-lowest CJTP but falls below the 161.36M median burden, so it receives a targeted reliability review rather than the same aggregate-burden claim. [3, 6]

![Operational Priorities dashboard](../dashboards/screenshots/Operational%20Priorities.png)

### Incident patterns are clues, not explanations

The largest 2025 weekday delay-incident categories were **Police & Medical (16,215)** and **Infrastructure & Equipment (13,692)**. Across 1,101 line-months with incident records, the line-and-month-adjusted incident-count/CJTP correlation was **−0.411**. The association can help locate months for review, but different source clocks, line exposure, incident severity, and common disruptions prevent a causal reading. The separate major-incident counts are not added to delay incidents. [2, 5]

## Recommended next diagnostic cycle

1. **F:** examine months and periods where CJTP and AJT worsened together; compare platform versus train time and the 91.63% peak service-delivery ratio with scheduled service and event records.
2. **B and Q:** review persistent poor customer outcomes. For B, test whether the 2025 improvement from 2024 continued and which problems remain. For Q, locate the high passenger-time burden by period and place before selecting an operational response.
3. **D:** examine low-CJTP months, stations, and periods as a distinct reliability problem. Its fifth baseline rank is less stable across weights than the F/B/Q shortlist.
4. **Measure before changing service:** obtain train- or service-exposure denominators for incident rates, confirm the MTA's convention for absent major-incident rows, and use event-level records to assess whether an operational change could affect the observed customer outcome. [3, 5, 6]

## Limits on interpretation

The customer metrics are model estimates for weekday unlinked train trips during the published hours. Net additional time is signed; it excludes weekends, late nights, and complete journeys with transfers. The 42nd Street Shuttle's incomplete 2022 coverage affects the all-observation year comparison. Incident counts are neither severity measures nor exposure-adjusted line risk rates. Service Delivered reflects selected peak timepoints and can exceed 100%; 42 source rows do so. Missing incident and sparse major-incident cells are not verified zeros. The score's weights and median cutoffs are analytical choices, not MTA policy. This static 2022–2025 snapshot should be refreshed before current operational use. [1–4, 5–7]

## Sources and reproducibility

1. [MTA Customer Journey-Focused Metrics](https://data.ny.gov/d/r7qk-6tcy) and local source Overview/Data Dictionary under `data/documentation/`.
2. [MTA Delay-Causing Incidents](https://data.ny.gov/d/g937-7k7c), [Major Incidents](https://data.ny.gov/d/ereg-mcvp), and [Service Delivered](https://data.ny.gov/d/32ch-sei3); local source documentation under `data/documentation/`.
3. [2025 priority scorecard](../data/analysis/line_priority_2025.csv) and [priority method](PRIORITIZATION_METHOD.md).
4. [Source manifest](../data/source_manifest.json): dataset IDs, extraction URLs, row counts, retrieval timestamp, and SHA-256 hashes.
5. [Exploratory findings](EDA_FINDINGS.md), [KPI definitions](KPI_DEFINITIONS.md), and [analytical limitations](ANALYTICAL_LIMITATIONS.md).
6. [Priority recommendations](PRIORITY_RECOMMENDATIONS.md) and [sensitivity validation](../data/analysis/priority_validation.json).
7. [Phase 2 validation](../data/validation/VALIDATION_SUMMARY.md), [Power BI reporting validation](../data/powerbi/reporting_validation.json), and executable scripts under `src/`.

The [repository README](../README.md) gives the commands to reproduce the pipeline and open the portable Power BI project. The report is a portfolio analysis and does not represent an official MTA recommendation.

## Reproduction and audit trail

| Stage | Main artifact | Check |
| --- | --- | --- |
| Acquisition | `data/source_manifest.json` and four raw CSVs | Exact MTA IDs, retrieval time, row counts, and SHA-256 hashes |
| Cleaning and SQL model | `data/processed/`, `sql/`, `data/validation/` | 51 of 51 source/model checks passed; 21,475 raw rows reconcile |
| Analysis and priorities | `data/analysis/`, `notebooks/`, `reports/` | Weighted KPI calculations and seven priority checks passed |
| Dashboard | `data/powerbi/`, `dashboards/TransitPulse.pbip` | 10 of 10 reporting checks passed; four pages rendered in Desktop |

From a clone, install `requirements.txt` and open `dashboards/TransitPulse.pbip` to inspect the fixed reporting snapshot without a database login. To rerun the full SQL pipeline, set up the local PostgreSQL cluster and execute the phase commands in the README. Updating the MTA extract creates a new snapshot and requires a fresh validation and narrative review before republishing.
