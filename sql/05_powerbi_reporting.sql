-- Import-ready reporting layer. Each fact has a declared, non-overlapping grain.
-- Dimensions filter facts one way. No fact-to-fact joins are intended.
CREATE OR REPLACE VIEW mta.rpt_dim_month AS
SELECT month, extract(year FROM month)::int AS year,
       extract(month FROM month)::int AS month_number,
       to_char(month, 'Mon YYYY') AS month_label
FROM mta.dim_calendar_month
WHERE month >= date '2022-01-01' AND month < date '2026-01-01';

CREATE OR REPLACE VIEW mta.rpt_dim_line AS
SELECT DISTINCT comparison_line AS line_id,
       CASE WHEN comparison_line = 'NW' THEN 'N/W comparison group'
            ELSE comparison_line END AS line_label,
       comparison_line LIKE 'S %' AS is_shuttle
FROM mta.fact_customer_journey;

CREATE OR REPLACE VIEW mta.rpt_customer_month_line_period AS
SELECT month, comparison_line AS line_id, period,
       sum(num_passengers) AS passenger_trips,
       sum(over_five_mins) AS over_five_trips,
       sum(total_apt) AS platform_minutes,
       sum(total_att) AS train_minutes,
       sum(total_apt + total_att) AS net_additional_passenger_minutes
FROM mta.fact_customer_journey
GROUP BY month, comparison_line, period;

CREATE OR REPLACE VIEW mta.rpt_delay_month_line_category AS
SELECT month, comparison_line AS line_id, day_type,
       CASE WHEN reporting_category = '' THEN '(Unspecified)' ELSE reporting_category END AS delay_category,
       sum(incidents) AS delay_incidents
FROM mta.fact_delay_incidents
GROUP BY month, comparison_line, day_type, reporting_category;

CREATE OR REPLACE VIEW mta.rpt_major_month_line_category AS
SELECT month, comparison_line AS line_id, day_type, category AS major_category,
       sum("count") AS major_incidents
FROM mta.fact_major_incidents
WHERE comparison_line <> ''
GROUP BY month, comparison_line, day_type, category;

CREATE OR REPLACE VIEW mta.rpt_service_month_line_daytype AS
SELECT month, comparison_line AS line_id, day_type,
       sum(num_sched_trains) AS scheduled_peak_trains,
       sum(num_actual_trains) AS actual_peak_trains,
       count(*) FILTER (WHERE service_delivered_percent > 100) AS rows_over_100_percent
FROM mta.fact_service_delivered
GROUP BY month, comparison_line, day_type;

CREATE OR REPLACE VIEW mta.rpt_dim_delay_category AS
SELECT DISTINCT delay_category FROM mta.rpt_delay_month_line_category;

CREATE OR REPLACE VIEW mta.rpt_dim_major_category AS
SELECT DISTINCT major_category FROM mta.rpt_major_month_line_category;
