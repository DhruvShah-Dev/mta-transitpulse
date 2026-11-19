-- Annual weekday/weekend peak service delivery from train counts; >100% retained.
SELECT comparison_line AS line_id, EXTRACT(YEAR FROM month)::int AS year,
       day_type, count(DISTINCT month) AS months_observed,
       sum(num_sched_trains) AS scheduled_trains,
       sum(num_actual_trains) AS actual_trains,
       100.0 * sum(num_actual_trains) / NULLIF(sum(num_sched_trains), 0) AS service_delivered_percent,
       count(*) FILTER (WHERE service_delivered_percent > 100) AS rows_over_100_percent
FROM mta.fact_service_delivered
GROUP BY comparison_line, EXTRACT(YEAR FROM month)::int, day_type
ORDER BY year, line_id, day_type;
