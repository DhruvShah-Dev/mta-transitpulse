-- Weekday incident categories by comparison line; blank zero rows excluded.
SELECT comparison_line AS line_id, EXTRACT(YEAR FROM month)::int AS year,
       reporting_category, sum(incidents) AS weekday_incidents,
       count(DISTINCT month) AS months_with_source_rows
FROM mta.fact_delay_incidents
WHERE day_type = 1 AND reporting_category <> ''
GROUP BY comparison_line, EXTRACT(YEAR FROM month)::int, reporting_category
ORDER BY year, line_id, weekday_incidents DESC;
