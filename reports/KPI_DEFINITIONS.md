# MTA TransitPulse KPI definitions

**Decision:** identify lines to investigate for poor passenger experience and large total time burden. Review monthly trends and complete calendar-year comparisons; keep line-level source coverage visible.

| Role | KPI | Calculation | Unit / direction | Source and scope |
| --- | --- | --- | --- | --- |
| Primary | Customer Journey Time Performance (CJTP) | `100 × (1 − Σ over_five_mins / Σ num_passengers)` | Percent; higher is better | MTA customer estimate, weekday 6 AM–11 PM, unlinked train trips |
| Primary | Additional Journey Time (AJT) | `(Σ total_apt + Σ total_att) / Σ num_passengers` | Net minutes per estimated trip; lower is better | Same customer population; signed metric |
| Primary | Net additional passenger minutes | `Σ total_apt + Σ total_att` | Net passenger minutes; lower is better | Same population; volume-sensitive |
| Driver | Additional Platform Time (APT) | `Σ total_apt / Σ num_passengers` | Minutes per trip | Waiting component of AJT |
| Driver | Additional Train Time (ATT) | `Σ total_att / Σ num_passengers` | Signed minutes per trip | Onboard component of AJT |
| Diagnostic | Weekday delay-causing incidents | `Σ incidents` for `day_type=1`, excluding only blank zero-category rows from category displays | Count; not an exposure-adjusted rate | MTA incident source, all weekday hours |
| Diagnostic | Weekday major incidents | `Σ count` for `day_type=1`, where a line is assigned | Count; sparse positive-event table | MTA major-incident source; separate from broader incidents |
| Diagnostic | Weekday peak Service Delivered | `100 × Σ num_actual_trains / Σ num_sched_trains` | Percent, may exceed 100 | MTA selected peak timepoints; not full-day service |

## Aggregation and comparison rules

- Recompute percentages and per-trip averages from summed numerators and denominators. Do not average monthly or peak/off-peak percentages.
- Use published service IDs for customer-only rankings. Combine N and W into the `NW` comparison group when adding incidents, because incident sources publish them together under N. `JZ` is already combined. Do not treat `NW` as a separate subway route.
- Compare full 12-month years; the 42nd Street Shuttle lacks customer rows in January–February 2022 and is excluded from 2022-versus-2025 like-for-like system comparisons.
- Keep absent incident and major-incident records null. The missing April 2025 42nd Street Shuttle incident row cannot be read as zero. A major-incident zero can be asserted only after the MTA confirms absence means no events.
- Do not cap Service Delivered above 100%; the count ratio exceeds 100% in 42 source rows. Show this source exception in diagnostic views.
- Raw incident counts are useful for workload and pattern review, but do not measure incident risk across lines without a valid train/service exposure denominator. A percentage-point CJTP change is not a percentage change.

## Prioritization approach

The 2025 scorecard publishes **separate ranks** for low CJTP and high net passenger minutes. The first investigation shortlist is the intersection of the worst six of 23 comparison groups on both measures. This is an explicit screening rule, not a weighted composite score or resource-allocation formula. Before setting a composite priority score, test stability across years, plausible weights, and treatment of small shuttle services; obtain a valid exposure denominator if incident rate is to influence the score.

## Source and implementation

Sources: the four MTA dataset pages in [README.md](../README.md) and local Overview/Data Dictionary PDFs under `data/documentation/`. Exact formulas appear in [SQL analysis queries](../sql/analysis/), with calculated outputs under `data/analysis/`.
