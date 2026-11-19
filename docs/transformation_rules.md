# Transformation rules and source exceptions

## Inputs and grain

All four raw CSVs are MTA portal extracts for January 2022 through December 2025. The cleaned facts retain all 21,475 source rows and a 1-based `source_row_id` tied to raw CSV order. The original `line`, metric fields, and source values remain in the processed files. Dates are ISO calendar-month starts.

| Fact | Source grain | Key |
| --- | --- | --- |
| Customer journey | month × division × line × peak/offpeak | `month, division, line, period` |
| Delay incidents | month × division × line × day type × category | `month, division, line, day_type, reporting_category` |
| Major incidents | month × division × line × day type × category | `month, division, line, day_type, category` |
| Service delivered | month × division × line × day type | `month, division, line, day_type` |

## Line mapping

`line_mapping.csv` is the source-specific mapping contract. `canonical_line` identifies the service represented by the row; `comparison_line` is the cross-source aggregation group. N and W are separate in Customer Journey and Service Delivered, but the incident sources publish them together under N. Those incident rows map to canonical/comparison `NW`, and separate N/W rows map to comparison `NW` only. This avoids assigning the combined incident count to N alone. J and Z are published as `JZ` in every source here.

The Service Delivered source switches from descriptive shuttle labels to GTFS IDs in September 2024. `FS → S Fkln`, `GS → S 42nd`, and `H → S Rock` are verified against the [MTA subway GTFS feed](https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip); the three relevant route records are saved in `data/documentation/mta_gtfs_shuttle_routes.csv`. The source-specific MTA Overview PDFs also document the N/W combination.

Eight Major Incidents rows have blank source line and division. Their canonical line is `UNASSIGNED`; their comparison line remains blank. They stay in the fact table and outside the line-level mart. The MTA's Major Incidents Overview says non-revenue-location incidents can lack a line.

## Metric units and scope

- Customer journey fractions `customer_journey_time` and `over_five_mins_perc` are multiplied by 100 to make `cjt_percent` and `over_five_percent`. APT and ATT are minutes per estimated unlinked train trip. `total_apt + total_att` is net additional passenger minutes. These customer measures cover weekday 6 AM–11 PM, with peak/offpeak detail; the MTA does not calculate them for weekends or late nights.
- Delay-causing incident counts and major-incident counts are not additive views of the same phenomenon. The monthly mart includes **weekday** incident counts, although these still cover more hours than customer journey metrics. Major-incident categories do not map one-to-one to delay categories.
- `service_delivered_percent = 100 × num_actual_trains / num_sched_trains`. For all 2,212 rows, the source `service_delivered` field is the count ratio divided by 100. The original field is preserved. Service Delivered covers selected peak timepoints and is not full-day service.
- The Service Delivered count ratio exceeds 100% in 42 rows, up to 104.295%. Those rows have actual counts greater than scheduled counts. They are valid arithmetic results and are **flagged, not capped**. Whether the extra operated trains reflect added service or source corrections requires MTA clarification.
- All 2,149 blank Delay Incidents category rows have zero incidents. They remain in the fact table and have `category_status=uncategorized_zero`; exclude them from category-mix displays.
- Customer Journey has no 42nd Street Shuttle rows in January–February 2022. April 2025 has two customer rows for that shuttle but no Delay Incidents row. The mart keeps that incident count null. Major Incidents is a sparse positive-event table; absent line-months remain null until the source's zero-record convention is confirmed.

## Monthly mart

`mta.mart_monthly_line_performance` uses Customer Journey line-months as its base. It aggregates each fact independently by `month, comparison_line` before joining, so category and day-type rows cannot multiply passenger metrics. Passenger averages and CJTP use passenger totals as denominators; Service Delivered uses scheduled-train totals. `has_*` flags distinguish missing source records from zero counts. The mart combines N/W customer and service records to match incident reporting, but source-specific facts retain separate N and W rows.

The mart supports descriptive comparisons and associations. Incident attribution is partly judgmental and changed over time, so correlations do not establish causes.
