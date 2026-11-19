# 2025 operational prioritization method

## Decision and population

This is a screening model for choosing subway comparison groups for further investigation. It does not estimate a causal effect, prescribe investments, or represent official MTA priorities. The 2025 customer population is estimated unlinked weekday train trips from 6 AM to 11 PM. There are 23 comparison groups with 12 customer months each. `NW` combines N and W for cross-source comparison because the incident source reports them together; it is not a new route. The three shuttle groups remain visible but are small relative to the main routes.

`sql/analysis/07_priority_components.sql` builds one row per 2025 group from the PostgreSQL facts. `src/build_priority_scorecard.py` creates `data/analysis/07_priority_components.csv`, the final scorecard, and metadata. All historical CJTP and AJT figures are based on complete 12-month years; the 42nd Street Shuttle has no 2022 value under that rule.

## Inputs and aggregation

| Input | Unit and rule | Role |
| --- | --- | --- |
| CJTP | `100 × (1 − sum(over_five_mins) / sum(num_passengers))`; percent, higher is better | Scored customer reliability |
| Net additional passenger time | `sum(total_apt + total_att)`; **signed** minutes, higher burden is worse | Scored passenger burden |
| AJT | `sum(total_apt + total_att) / sum(num_passengers)`; signed minutes per estimated trip | Diagnostic only; overlaps with net minutes |
| Passenger trips | `sum(num_passengers)`; estimated unlinked trips | Context for aggregate burden; already affects net minutes |
| Weekday peak Service Delivered | `100 × sum(num_actual_trains) / sum(num_sched_trains)`; percent, higher is better | Scored operational proxy |
| Weekday delay-causing incidents | `sum(incidents)` for `day_type=1`; count across weekday hours | Diagnostic only |
| Weekday major incidents | `sum(count)` for assigned `day_type=1` rows; count | Separate diagnostic only; sparse positive-event source |

No monthly percentage or AJT is averaged. Negative passenger-time components are retained. Service Delivered observations above 100% remain unchanged in source and annual ratios; no capping is applied. The annual service percentage reflects selected peak timepoints, not all-day service quality. Annual service rows above 100% are counted in the input table for audit. Incidents are not scored because the available scheduled-train denominator covers peak service, whereas incident counts cover all weekday hours. The two incident datasets are never added together; they may describe related events. Missing incident months and absent major-incident records remain distinguishable from zero counts. April 2025 42nd Street Shuttle delay-incident data is missing.

## Normalization, weights, and quadrants

Each scored input becomes an observed-rank percentile across the 23 groups, with best = 0 and worst = 100, using average ranks for ties. Lower CJTP and Service Delivered receive higher concern scores; higher net minutes receive higher burden scores. This uses order, not the size of gaps, and can shift if the eligible population changes. All three inputs must be present to calculate a composite score.

The proposed baseline score is `0.40 × reliability concern + 0.40 × passenger burden + 0.20 × operational risk`. Five explicit scenarios are in `priority_metadata.json`: baseline (40/40/20), equal (⅓ each), reliability focused (60/25/15), burden focused (25/60/15), and service focused (25/25/50). These are analytical assumptions, not official MTA weights. Higher score means higher investigation priority; ranks use competition ranking with line ID as a deterministic display tie break. No fixed action threshold is inferred from the scores.

The matrix uses the 2025 medians as descriptive cutoffs: CJTP **84.9498%** and net additional passenger time **161.361 million minutes**. CJTP below its median is “poor reliability”; burden above its median is “high burden.” Exact equality is placed in the better/lower side. The cutoffs are not service targets. Bubble area represents estimated passenger trips. F, Q, B, and D are labeled on the chart based on their calculated coordinates.

An unweighted customer-outcome Pareto check sits beside the composite. A group is dominated if another has at least as low CJTP and at least as high net minutes, with one strict difference. The check excludes Service Delivered; it does not substitute for incident or line-specific investigation.

## Interpretation guardrails

- CJTP, AJT, and net minutes all reflect journey outcomes. Scoring only CJTP and net minutes avoids adding AJT as a third expression of the same customer experience. Passenger volume is shown separately because it is built into aggregate net minutes.
- The scoring model uses 2025 levels. Historical CJTP and AJT, including 2024-to-2025 and 2022-to-2025 changes, are diagnostic context rather than extra score components, so a persistent low level is not counted again as a trend penalty.
- The shuttle groups are low on the baseline score because their aggregate burden is small; that does not rule out a local reliability issue. If the decision is about equitable route coverage, add a separate service-class review.
- Service Delivered is a proxy for operational risk, not proof that missed peak trains caused journey outcomes. It may exceed 100% and is not capped.
- An incident count is workload evidence, not a cross-line risk rate. Major-incident missing records cannot be assumed to mean zero events without a source guarantee.
- The source populations and time windows differ. Investigate causes with route, period, location, and event-level evidence before choosing an intervention.

## Reproduction

From the project root: `python src/build_priority_scorecard.py`, `python src/create_priority_notebook.py`, then `python src/validate_priority.py`. The CSV, metadata, notebook, and validation JSON are saved project outputs; the local PostgreSQL service is started automatically by the scorecard script.
