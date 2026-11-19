# Project plan: NYC Subway Reliability & Passenger Impact Intelligence

## Decision question

Which subway lines had the greatest passenger journey-time burden and reliability problems in 2022–2025, how did those patterns change, and which operational incident categories warrant investigation? The output will support line prioritization, not causal claims.

## Scope and analytical rules

- **Baseline:** January 2022–December 2025, all 48 calendar months. Keep 2026 outside the baseline until a complete, validated extension is available.
- **Primary outcome:** MTA customer journey measures for weekday 6 AM–11 PM only. Keep peak and off-peak detail. These are estimated **unlinked train trips**, not complete multi-train journeys.
- **Passenger burden:** Calculate net additional passenger minutes as `total_apt + total_att`, or equivalently passenger-weighted `APT + ATT`. Negative ATT and net values are valid. For a positive-only burden measure, define and label a separate metric after checking whether the aggregated data can support it; do not silently clamp negatives.
- **CJTP:** Weight by `num_passengers` (or derive from `over_five_mins` and `num_passengers`) when aggregating peak/off-peak or months. Do not take a simple mean of percentages.
- **Incidents:** Keep delay-causing and major incidents as separate measures. Major incidents exclude some causes and can overlap with the broader incident view. Preserve category and day type tables before monthly aggregation.
- **Service delivered:** Use `num_actual_trains / num_sched_trains` for an interpretable fraction, weighted by scheduled trains across day types. The raw `service_delivered` field equals that ratio divided by 100 in this snapshot; validate the source convention on refresh. Service Delivered reflects service at peak timepoints, not full-day service.
- **Comparability:** Customer journey measures exclude weekends and late nights. Use weekday (`day_type=1`) incidents for customer outcome associations, with the remaining hour mismatch stated. Compare weekday peak Service Delivered with customer peak only, and retain weekend service as a separate view.
- **Line mapping:** Delay-causing and major-incident sources combine N and W under `N`; customer journey and Service Delivered have separate N and W rows. For cross-source comparisons, either combine customer N+W with passenger weights and service N+W with scheduled-train weights, or exclude that group from single-line association tests. Do not attribute a combined incident count to N alone. `JZ` is already combined across sources. Service Delivered switches shuttle codes in September 2024 (`FS`, `GS`, `H`); verify the code-to-shuttle mapping against an authoritative source before joining those rows.
- **Missingness:** Keep source absence distinct from zero. Confirm whether missing Major Incidents line-months mean zero before filling them. Keep eight major-incident rows without a line in a separate system/unassigned bucket; do not allocate them to lines.

## Work sequence

### 1. Validate and document the raw data

Create a repeatable profile in `src/` covering schemas, row counts, monthly coverage, missing and duplicate keys, numeric ranges, source identities, and line-code changes. Reconcile counts with the API and record exceptions. Review the eight MTA PDFs for metric definitions and reporting limits. Produce a short data-quality decision log.

**Exit gate:** each source has a documented grain, key, period, coverage, and treatment for missing or unusual values.

### 2. Build clean detail tables and a monthly mart

Standardize dates and line IDs with an explicit, source-specific mapping table. Preserve customer peak/off-peak, incident category/day type, major category/day type, and service day type as separate detail tables. Aggregate each source to the comparison grain before joining; never join raw category rows directly to customer rows. Build a line-month mart with coverage flags, customer weighted metrics, weekday incident counts, major-incident counts, and applicable service measures.

**Exit gate:** every mart key is unique; totals reconcile to source detail; joins do not multiply rows; missingness remains visible.

### 3. Analyze reliability and passenger impact

Measure trends, seasonality, peak/off-peak differences, net passenger minutes, and consistent poor performance. Compare incident composition and test monthly associations using comparable line groups and periods. Normalize incident counts only if a valid service exposure denominator is identified; do not present raw counts as an equivalent risk rate across lines. Check robustness to high-volume lines, small shuttle services, missing periods, and changes in incident attribution.

**Exit gate:** each ranking has a clear metric definition, time window, coverage rule, and sensitivity check.

### 4. Deliver the decision tools

Create a Power BI line scorecard and trend/incident views, plus an analytical report with prioritized lines, supporting evidence, uncertainty, and recommended operational follow-up. Include a methodology and source note so users can distinguish customer experience, incident counts, and service delivery.

**Exit gate:** the dashboard and report answer the project decision question with traceable figures and no unsupported causal interpretation.

## Planned outputs

| Phase | Deliverable |
| --- | --- |
| Data validation | Source profile, data-quality decision log, line mapping |
| Preparation | Clean detail tables, monthly line mart, SQL schema and checks |
| Analysis | Weighted KPIs, trends, associations, prioritization method |
| Presentation | Power BI dashboard and concise analytical report |

## Source references

The four dataset pages and their local Overview/Data Dictionary PDFs are listed in [README.md](README.md). Exact extraction URLs, checksums, and retrieval time are recorded in [source_manifest.json](data/source_manifest.json).

## Phase 2 status

Completed: four cleaned fact CSVs, explicit source-specific line mapping, PostgreSQL tables and monthly view, and 51 automated local validation checks. The dedicated local PostgreSQL load passed SQL reconciliation. Source exceptions and remaining analytical interpretation limits are recorded in [transformation_rules.md](docs/transformation_rules.md) and the [validation summary](data/validation/VALIDATION_SUMMARY.md).

## Phase 3 status

Completed: six PostgreSQL analysis queries, annual customer and 2025 comparison-group scorecards, monthly relationship summaries, two executed notebooks, and a findings report. Twelve Phase 3 validation checks passed. The initial F/Q investigation shortlist uses the intersection of two published ranks; a weighted priority model is deferred to Phase 4, and Power BI remains Phase 5.
