-- One row per 2025 comparison group. Historical customer measures are full-year
-- only; source absence remains NULL. Incident sources are not added together.
WITH customer_year AS (
    SELECT comparison_line AS line_id, extract(year FROM month)::int AS year,
           count(DISTINCT month) AS customer_months,
           sum(num_passengers) AS passenger_trips,
           sum(over_five_mins) AS trips_over_five_minutes,
           100.0 * (1 - sum(over_five_mins) / nullif(sum(num_passengers), 0)) AS cjt_percent,
           sum(total_apt) AS platform_minutes,
           sum(total_att) AS train_minutes,
           sum(total_apt + total_att) AS net_additional_passenger_minutes,
           sum(total_apt + total_att) / nullif(sum(num_passengers), 0) AS ajt_minutes_per_trip
    FROM mta.fact_customer_journey
    GROUP BY 1, 2
), customer_2025 AS (
    SELECT * FROM customer_year WHERE year = 2025
), history AS (
    SELECT line_id,
           max(cjt_percent) FILTER (WHERE year = 2022 AND customer_months = 12) AS cjt_2022_percent,
           max(cjt_percent) FILTER (WHERE year = 2023 AND customer_months = 12) AS cjt_2023_percent,
           max(cjt_percent) FILTER (WHERE year = 2024 AND customer_months = 12) AS cjt_2024_percent,
           max(ajt_minutes_per_trip) FILTER (WHERE year = 2022 AND customer_months = 12) AS ajt_2022_minutes_per_trip,
           max(ajt_minutes_per_trip) FILTER (WHERE year = 2023 AND customer_months = 12) AS ajt_2023_minutes_per_trip,
           max(ajt_minutes_per_trip) FILTER (WHERE year = 2024 AND customer_months = 12) AS ajt_2024_minutes_per_trip
    FROM customer_year GROUP BY line_id
), incidents AS (
    SELECT comparison_line AS line_id, count(DISTINCT month) AS incident_months,
           sum(incidents) AS weekday_delay_incidents
    FROM mta.fact_delay_incidents
    WHERE day_type = 1 AND month >= date '2025-01-01' AND month < date '2026-01-01'
    GROUP BY 1
), major AS (
    SELECT comparison_line AS line_id, count(DISTINCT month) AS major_incident_record_months,
           sum("count") AS weekday_major_incidents
    FROM mta.fact_major_incidents
    WHERE day_type = 1 AND comparison_line <> ''
      AND month >= date '2025-01-01' AND month < date '2026-01-01'
    GROUP BY 1
), service AS (
    SELECT comparison_line AS line_id, count(DISTINCT month) AS service_months,
           sum(num_sched_trains) AS scheduled_peak_trains,
           sum(num_actual_trains) AS actual_peak_trains,
           100.0 * sum(num_actual_trains) / nullif(sum(num_sched_trains), 0) AS service_delivered_percent,
           count(*) FILTER (WHERE service_delivered_percent > 100) AS service_rows_over_100_percent
    FROM mta.fact_service_delivered
    WHERE day_type = 1 AND month >= date '2025-01-01' AND month < date '2026-01-01'
    GROUP BY 1
)
SELECT c.line_id, c.customer_months, c.passenger_trips, c.trips_over_five_minutes,
       c.cjt_percent, c.platform_minutes, c.train_minutes,
       c.net_additional_passenger_minutes, c.ajt_minutes_per_trip,
       h.cjt_2022_percent, h.cjt_2023_percent, h.cjt_2024_percent,
       h.ajt_2022_minutes_per_trip, h.ajt_2023_minutes_per_trip, h.ajt_2024_minutes_per_trip,
       c.cjt_percent - h.cjt_2024_percent AS cjt_yoy_change_pp,
       c.cjt_percent - h.cjt_2022_percent AS cjt_since_2022_change_pp,
       i.incident_months, i.weekday_delay_incidents,
       m.major_incident_record_months, m.weekday_major_incidents,
       s.service_months, s.scheduled_peak_trains, s.actual_peak_trains,
       s.service_delivered_percent, s.service_rows_over_100_percent
FROM customer_2025 c
LEFT JOIN history h USING (line_id)
LEFT JOIN incidents i USING (line_id)
LEFT JOIN major m USING (line_id)
LEFT JOIN service s USING (line_id)
ORDER BY c.line_id;
