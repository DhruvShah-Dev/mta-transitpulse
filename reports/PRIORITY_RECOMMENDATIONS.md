# 2025 subway investigation priorities

**Decision:** begin a focused diagnostic review of F, Q, and B, with a separate reliability review of D. These are investigation priorities, not a forecast of intervention benefit. The score uses proposed 40% reliability, 40% passenger burden, and 20% weekday peak Service Delivered weights across 23 comparison groups. Consult [the method](PRIORITIZATION_METHOD.md) before using ranks for resource allocation.

## Evidence at a glance

| Group | 2025 CJTP | Net additional passenger minutes | AJT, min/trip | Weekday delay incidents | Weekday peak Service Delivered | Baseline rank | Rank range across five scenarios | Matrix position |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| F | 81.75% | 232.0m | 1.91 | 4,021 | 91.63% | 1 | 1–2 | High burden / poor reliability |
| Q | 79.84% | 203.6m | 2.24 | 2,823 | 94.48% | 3 | 2–4 | High burden / poor reliability |
| B | 78.74% | 173.5m | 2.57 | 2,087 | 91.11% | 2 | 1–3 | High burden / poor reliability |
| D | 79.63% | 148.1m | 2.04 | 2,774 | 93.39% | 5 | 4–10 | Lower burden / poor reliability |

Net minutes are a **signed model estimate** for the stated passenger population. The matrix divides lines at the sample medians: 84.95% CJTP and 161.36m net minutes. F, Q, and B form the unweighted customer-outcome Pareto frontier. D is dominated by B on the two customer outcome measures, but its low CJTP warrants a targeted review. The fifth scenario gives D rank 10, showing that its composite place depends more on weights than the F/Q/B shortlist.

## Proposed investigation sequence

1. **F: review both experience and service supply.** F has the largest net burden (232.0m), CJTP 81.75%, and a 91.63% peak delivery ratio. Examine the months, periods, and incident categories behind its 4,021 weekday delay-causing incidents, then check whether poor months and lower peak delivery co-occur. Its 2025 CJTP improved only 0.38 percentage points from 2024, while AJT rose from 1.81 to 1.91 minutes per trip. The aggregate pattern warrants localization before any operational change.
2. **Q: review high burden with weak journey reliability.** Q has 203.6m net minutes, CJTP 79.84%, and AJT 2.24 minutes per trip. Its CJTP improved 0.20 percentage points from 2024. Identify whether platform or train time drives the burden by period and location, then examine incident records and planned service where those problems are concentrated. Q remains rank 2–4 across all five scenarios.
3. **B: investigate the poorest customer experience.** B has the lowest CJTP (78.74%) and highest AJT (2.57 minutes per trip) of the 23 groups, with 173.5m net minutes and 91.11% peak delivery. It ranks 1–3 under every weight scenario and shares the high-burden/poor-reliability quadrant. Its CJTP improved 2.45 percentage points versus 2024, so the review should test whether the improvement continued and what residual problems remain.
4. **D: run a targeted reliability diagnostic.** D has the second-lowest CJTP (79.63%) and 2.04 AJT minutes per trip, but 148.1m net minutes is below the sample burden median. Its CJTP improved 2.69 percentage points from 2024. Review station, period, and category evidence for persistent poor trips; keep its lower and weight-sensitive aggregate priority distinct from the F/Q/B customer-burden shortlist.

**Secondary watchlist:** R ranks fourth at baseline and 3–5 across scenarios; its 90.33% peak delivery is the lowest of the 23 groups, and its net minutes are 180.3m. Check whether service delivery is sustained below plan at specific peaks. NW ranks 4–7 across scenarios and has 198.0m net minutes; because N and W are combined for source comparability, inspect the two published customer services separately before assigning a route owner.

## Limits on the decision

The weights and median cutoffs are analytical choices. Composite ranks compress differences in magnitude, and a percentile may shift when the population changes. Raw delay incidents are not cross-line risk rates, and major incidents are a separate sparse source, so neither is added to the score. Service Delivered covers selected peak timepoints, while CJTP and incidents cover different periods. No co-occurrence proves causality. Investigations should use time, location, route, and event-level operational records before a budget or schedule change. The three shuttles remain in the scorecard but need a separate service-class review if the decision concerns minimum coverage or equity.

The underlying line-level figures, all five rank scenarios, Pareto flags, and source coverage are in [`line_priority_2025.csv`](../data/analysis/line_priority_2025.csv). The executed [notebook](../notebooks/03_priority_analysis.ipynb) contains the priority matrix and sensitivity charts.
