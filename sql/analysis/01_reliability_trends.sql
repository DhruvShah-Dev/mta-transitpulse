-- Annual passenger-weighted customer reliability by published service.
SELECT canonical_line AS line_id, EXTRACT(YEAR FROM month)::int AS year,
       count(DISTINCT month) AS months_observed,
       sum(num_passengers) AS passenger_trips,
       sum(over_five_mins) AS trips_over_five_minutes,
       100.0 * (1 - sum(over_five_mins) / NULLIF(sum(num_passengers), 0)) AS cjt_percent,
       sum(total_apt + total_att) / NULLIF(sum(num_passengers), 0) AS ajt_minutes_per_trip
FROM mta.fact_customer_journey
GROUP BY canonical_line, EXTRACT(YEAR FROM month)::int
ORDER BY year, cjt_percent, line_id;
