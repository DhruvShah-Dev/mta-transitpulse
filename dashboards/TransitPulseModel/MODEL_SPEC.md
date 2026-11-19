# TransitPulse Power BI model specification

**Status:** local reporting views and CSV mirrors are validated. The [TransitPulse PBIP](../TransitPulse.pbip) implements this Import model and four report pages; all pages have been rendered and checked in Power BI Desktop. Period: January 2022–December 2025.

## Source tables and grain

| Power BI table | PostgreSQL source / CSV mirror | Grain | Rows |
| --- | --- | --- | ---: |
| `rpt_dim_month` | `mta.rpt_dim_month` | month | 48 |
| `rpt_dim_line` | `mta.rpt_dim_line` | comparison group | 23 |
| `rpt_dim_delay_category` | `mta.rpt_dim_delay_category` | delay category | 7 |
| `rpt_dim_major_category` | `mta.rpt_dim_major_category` | major category | 6 |
| `rpt_customer_month_line_period` | `mta.rpt_customer_month_line_period` | month × group × period | 2,204 |
| `rpt_delay_month_line_category` | `mta.rpt_delay_month_line_category` | month × group × day type × category | 15,043 |
| `rpt_major_month_line_category` | `mta.rpt_major_month_line_category` | month × assigned group × day type × category | 1,912 |
| `rpt_service_month_line_daytype` | `mta.rpt_service_month_line_daytype` | month × group × day type | 2,153 |
| `rpt_priority_2025` | `mta.rpt_priority_2025` | 2025 comparison group | 23 |

Each table also has a local CSV at `data/powerbi/<table>.csv`; the manifest records row counts, columns, and SHA-256 hashes. The priority table is loaded from the validated Phase 4 CSV. `review_status` labels F/B/Q “First investigation” and D “Targeted reliability review.”

## Relationships

The PBIP has these **one-to-many, single-direction** dimension-to-fact relationships, with all active. Facts are not connected directly.

| One-side key | Many-side key | Applies to |
| --- | --- | --- |
| `rpt_dim_month[month]` | each monthly fact `[month]` | customer, delay, major, service |
| `rpt_dim_line[line_id]` | each fact `[line_id]` | customer, delay, major, service, priority |
| `rpt_dim_delay_category[delay_category]` | `rpt_delay_month_line_category[delay_category]` | delay only |
| `rpt_dim_major_category[major_category]` | `rpt_major_month_line_category[major_category]` | major only |

Do **not** relate `rpt_priority_2025` to month. It is a fixed annual scorecard. Use line slicers on all pages; year and month slicers affect the four operational facts only. The priority page shows a fixed 2025 label and should not reuse a general date slicer. Incident-category slicers affect only their matching incident fact; a CJTP card must not appear to change when an incident category is selected.

## Measure rules and formats

The 31 implemented expressions are maintained in [MEASURES.dax](MEASURES.dax) and attached to the customer fact table in the PBIP. Numeric source columns are hidden where measures provide the intended aggregation. CJTP and service ratios are percentages; table net minutes are shown in millions; AJT/APT/ATT are minutes per trip; and CJTP changes are percentage points.

- CJTP uses `1 − SUM(over_five_trips) / SUM(passenger_trips)`; it must never average monthly percentages.
- AJT/APT/ATT use summed minutes divided by summed passenger trips. Net time is signed and should not be clamped at zero.
- Weekday delay and major incidents are separate counts. A missing source row is blank, not zero. Major incidents have sparse positive-event rows, so blank does not prove no events.
- Service Delivered is actual/scheduled selected peak trains and can exceed 100%.
- Priority ranks and weights are fixed to 2025. DAX must not recompute them from filtered operational facts.

## Import connection

The PBIP embeds compressed snapshots of the nine validated CSV mirrors under `data/powerbi/` with typed columns. It opens and refreshes without PostgreSQL credentials or a computer-specific file path. The snapshot is fixed: after source changes, rerun `python src/build_powerbi_reporting.py`, then `python src/build_pbip_model.py`, apply external changes in Desktop, and refresh.

## Acceptance evidence

The PostgreSQL views, CSV mirrors, and Phase 4 priority import reproduce 2025 CJTP **85.4024%** (display 85.40%) and net additional passenger time **3.2405 billion minutes** (display 3.24B). Desktop renders these values. F, B, Q are ranks 1–3 and D is labeled for targeted reliability review. Desktop checks confirmed line, year, month, and delay-category selections, plus four-page navigation. The PBIR validator reports zero errors and warnings in offline schema mode; the reporting-data validator passes 10/10 checks.
