-- 2025 comparison-group scorecard. Ranks are separate, with no untested composite weight.
WITH annual_customer AS (
    SELECT comparison_line AS line_id, count(DISTINCT month) AS customer_months,
           sum(num_passengers) AS passenger_trips,
           sum(over_five_mins) AS trips_over_five_minutes,
           100.0 * (1 - sum(over_five_mins) / NULLIF(sum(num_passengers), 0)) AS cjt_percent,
           sum(total_apt) AS platform_minutes, sum(total_att) AS train_minutes,
           sum(total_apt + total_att) AS net_additional_passenger_minutes,
           sum(total_apt + total_att) / NULLIF(sum(num_passengers), 0) AS ajt_minutes_per_trip
    FROM mta.fact_customer_journey WHERE month >= '2025-01-01' AND month < '2026-01-01'
    GROUP BY comparison_line
), annual_incidents AS (
    SELECT comparison_line AS line_id, count(DISTINCT month) AS incident_months,
           sum(incidents) AS weekday_incidents
    FROM mta.fact_delay_incidents
    WHERE day_type = 1 AND month >= '2025-01-01' AND month < '2026-01-01'
    GROUP BY comparison_line
), annual_service AS (
    SELECT comparison_line AS line_id, count(DISTINCT month) AS service_months,
           sum(num_sched_trains) AS scheduled_trains,
           100.0 * sum(num_actual_trains) / NULLIF(sum(num_sched_trains), 0) AS service_delivered_percent
    FROM mta.fact_service_delivered
    WHERE day_type = 1 AND month >= '2025-01-01' AND month < '2026-01-01'
    GROUP BY comparison_line
)
SELECT c.*, i.incident_months, i.weekday_incidents, s.service_months,
       s.scheduled_trains, s.service_delivered_percent,
       rank() OVER (ORDER BY c.cjt_percent ASC) AS reliability_rank_worst_first,
       rank() OVER (ORDER BY c.net_additional_passenger_minutes DESC) AS burden_rank_highest_first
FROM annual_customer c
LEFT JOIN annual_incidents i USING (line_id)
LEFT JOIN annual_service s USING (line_id)
ORDER BY burden_rank_highest_first, line_id;
