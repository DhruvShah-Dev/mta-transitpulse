# Phase 2 validation summary

The local cleaning and reconciliation run passed **51 of 51 automated checks**. Four processed facts contain exactly **21,475 rows**, matching the four raw CSVs (2,300 customer, 15,043 delay, 1,920 major, 2,212 service). Source hashes, schemas, 48-month coverage, keys, mapping coverage, metric identities, count signs, and weighted mart aggregations were checked. The model produces **1,102 customer-based line-month comparison rows** with unique keys and unchanged customer passenger and minute totals.

Source exceptions remain visible:

- 42 Service Delivered records have actual trains above scheduled trains, yielding 100–104.295% after standardization. These are not clipped.
- April 2025 `S 42nd` has customer metrics but no weekday delay-incident record; the mart leaves the incident count null.
- Eight Major Incidents rows have no line. They remain in the fact table and are excluded only from line-level comparisons.
- Major Incidents has no explicit zero-event rows. Missing line-months stay null pending confirmation of the source convention.

The detailed machine-readable result is `validation_report.json`. The four fact tables, five reference/dimension tables, and monthly view were loaded into a dedicated local PostgreSQL instance. SQL-side reconciliation passed, and a direct query confirmed 1,102 view rows and a null incident value for April 2025 `S 42nd`. Local cluster management and connection commands are in the project README.
