# MTA TransitPulse | Subway Reliability & Passenger Impact

**Audience:** operations management, service planning, business intelligence. **Data:** January 2022–December 2025. **Status:** original design plan. The implemented four-page report is [TransitPulse.pbip](../TransitPulse.pbip); rendered page screenshots are in [screenshots](../screenshots/). The PBIP reflects validated source data and Desktop interaction checks. Details below record the initial wireframe, so some placements differ from the final report.

## Common layout

Use a 16:9 canvas, white or soft gray background, dark navy headings, blue for reference series, orange for watch items, and red for investigation priorities. Place page navigation across the top: **Overview · Line Performance · Diagnostics · Priorities**. Put the selected period and line group in the header; show the MTA source attribution and relevant caveat in a small but readable footer. Provide tooltip definitions for CJTP, AJT, net minutes, incidents, and Service Delivered. Keep chart axes and units explicit.

## 1. Executive Overview

```text
MTA TransitPulse                                      [Year: 2025] [Line: All]
Subway Reliability & Passenger Impact                 Overview | Lines | Diagnostics | Priorities
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ CJTP            │ Net minutes     │ CJTP YoY pp     │ 2025 priorities │
│ 85.40%          │ 3.24B           │ dynamic         │ F · B · Q       │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
┌─────────────────────────────────────┬─────────────────────────────────────┐
│ Monthly passenger-weighted CJTP     │ Monthly net passenger minutes       │
└─────────────────────────────────────┴─────────────────────────────────────┘
┌─────────────────────────────────────┬─────────────────────────────────────┐
│ 2025 investigation list: F, B, Q    │ D: targeted reliability review     │
└─────────────────────────────────────┴─────────────────────────────────────┘
```

Use dynamic CJTP/net cards tied to the selected year. The F/B/Q and D callouts must say **fixed 2025 priorities** and should not respond to a non-2025 year as though recalculated. Prefer no priority callout on a page filtered to another year, or show a fixed-baseline badge with an explicit 2025 label. A 2025 vs 2022 system comparison can appear only with the incomplete 2022 shuttle caveat.

## 2. Subway Line Performance

Line slicer (comparison group) and year slicer. Sort a horizontal line chart by CJTP ascending; show a separate net-minutes chart or toggle. Use monthly CJTP trend, APT/ATT per-trip breakdown, and a line table with CJTP, AJT, net minutes, passenger trips, and annual pp change. Keep APT and ATT signed where the source is signed; do not use a chart that hides negative ATT. For NW, explain that the comparison group combines N/W to match incident reporting.

## 3. Operational Diagnostics

Year, line, and **delay category** slicers. Show weekday delay incidents by category and month, peak Service Delivered trend, and a scatterplot of incident count vs CJTP at the monthly line grain. Mark the scatter as association only. A separate major-incident visual uses its own category slicer and never adds major counts to delay counts. Display incident coverage months for the selected line/year; April 2025 S 42nd is missing, not zero. Note that incident counts span all weekday hours while Service Delivered reflects selected peak timepoints; there is no valid shared train-exposure rate. Preserve service values above 100%.

## 4. Operational Priorities

Fixed **2025** label and line slicer; no year/month slicer. Scatter: X = 2025 CJTP (higher to the right), Y = net additional passenger minutes (higher upward), bubble size = passenger trips, color = computed quadrant. Add median dividers at 84.9498% and 161.361m minutes. Label F, B, Q, D. Below, show scorecard rank, scores (reliability, burden, service), review status, Pareto flag, and rank range across five weight scenarios. A small scenario comparison or slope chart shows F/B/Q stability and D's 4–10 range. Add text: **proposed analytical weights, not official MTA weights; scores are for investigation screening only**.

## Desktop verification after import

1. Confirm all nine tables load and the relationships in `MODEL_SPEC.md` are one-to-many and single direction.
2. With Year=2025 and all lines, verify CJTP 85.40%, net minutes 3.24B, and F/B/Q ranks 1/2/3. Verify D's status.
3. Filter a line and a year; check dynamic customer cards against `annual_customer_scorecard.csv`. Change to 2024 and ensure no 2025 card is labeled as current.
4. Filter a month; verify customer cards and incident coverage. On S 42nd / April 2025, incident count must be blank.
5. Change delay category; only delay visuals should respond. Check major category separately.
6. Verify navigation, tooltips, plot labels, negative train minutes, and service percentages above 100%.
