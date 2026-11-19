-- Annual passenger minutes and per-trip components; signed ATT is retained.
SELECT canonical_line AS line_id, EXTRACT(YEAR FROM month)::int AS year,
       sum(num_passengers) AS passenger_trips,
       sum(total_apt) AS platform_minutes,
       sum(total_att) AS train_minutes,
       sum(total_apt + total_att) AS net_additional_passenger_minutes,
       sum(total_apt) / NULLIF(sum(num_passengers), 0) AS apt_minutes_per_trip,
       sum(total_att) / NULLIF(sum(num_passengers), 0) AS att_minutes_per_trip,
       sum(total_apt + total_att) / NULLIF(sum(num_passengers), 0) AS ajt_minutes_per_trip
FROM mta.fact_customer_journey
GROUP BY canonical_line, EXTRACT(YEAR FROM month)::int
ORDER BY year, net_additional_passenger_minutes DESC;
