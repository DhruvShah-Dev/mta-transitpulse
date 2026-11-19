# Initial source profile

Snapshot retrieved 2026-11-19. All CSV row counts match the live API's count for January 2022–December 2025, and all four files contain 48 distinct months. These are preliminary checks for planning; the repeatable validation pipeline is the next phase.

| Source | Rows | Grain in raw file | Key duplicates | Coverage notes |
| --- | ---: | --- | ---: | --- |
| Customer journey | 2,300 | month × division × line × peak/offpeak | 0 | 24 lines; `S 42nd` absent Jan–Feb 2022 |
| Delay-causing incidents | 15,043 | month × division × line × day type × category | 0 | 23 line labels; 2,149 blank-category rows, all with zero incidents |
| Major incidents | 1,920 | month × division × line × day type × category | 0 | Only nonzero events represented; 8 rows have no line/division |
| Service delivered | 2,212 | month × division × line × day type | 0 | 27 line labels due to shuttle code change in Sep 2024 |

## Findings that affect modeling

1. **Line identifiers differ.** Incidents report N and W together under `N`; customer journey and service delivery separate them. Service delivery's shuttle labels change from `S Fkln`, `S 42nd`, and `S Rock` to `FS`, `GS`, and `H` in September 2024. The latter mapping needs explicit confirmation before a join.
2. **The sources cover different rider times.** Customer journey metrics cover weekdays from 6 AM to 11 PM. Incident tables include weekday and weekend; Service Delivered covers weekday and weekend peak timepoints. Cross-source associations must retain that scope difference.
3. **Some apparent nulls are meaningful.** Every blank incident category has `incidents=0`; these rows can be excluded from category mix without losing incident volume. The eight Major Incidents rows without a line must stay unassigned.
4. **The Service Delivered field has a scale mismatch.** For all 2,212 rows, the raw value equals `(num_actual_trains / num_sched_trains) / 100`. For example, 1,463 actual of 1,562 scheduled trains appears as `0.009366`, corresponding to 93.66% delivered. Use the count ratio to report service delivery and retain the raw field for audit.
5. **Customer fields reconcile.** `customer_journey_time` equals `1 - over_five_mins_perc`; `total_apt` and `total_att` equal their averages multiplied by `num_passengers` within floating-point precision. ATT is negative in 333 rows, so a negative net contribution is valid.
6. **Major Incident sparsity needs a rule.** Many line-months have no record, consistent with a positive-event table. Confirm that absence means zero before creating a complete monthly panel.

The MTA Overview PDFs explain that incident attribution is partly judgmental and category practice can change over time. Treat correlations as diagnostic associations, and check for classification changes before interpreting category trends.
