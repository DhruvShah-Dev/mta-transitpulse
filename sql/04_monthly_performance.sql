-- Customer weekday 6 AM-11 PM is the base. N and W are combined for source comparison.
CREATE OR REPLACE VIEW mta.mart_monthly_line_performance AS
WITH customer AS (
    SELECT month, comparison_line AS line_id,
           sum(num_passengers) AS passenger_trips,
           sum(total_apt) AS total_apt_minutes,
           sum(total_att) AS total_att_minutes,
           sum(total_apt + total_att) AS net_additional_passenger_minutes,
           sum(over_five_mins) AS over_five_trips,
           sum(total_apt) / NULLIF(sum(num_passengers), 0) AS apt_minutes_per_trip,
           sum(total_att) / NULLIF(sum(num_passengers), 0) AS att_minutes_per_trip,
           sum(total_apt + total_att) / NULLIF(sum(num_passengers), 0) AS ajt_minutes_per_trip,
           100 * (1 - sum(over_five_mins) / NULLIF(sum(num_passengers), 0)) AS cjt_percent
    FROM mta.fact_customer_journey
    GROUP BY month, comparison_line
), incidents AS (
    SELECT month, comparison_line AS line_id, sum(incidents) AS weekday_delay_incidents
    FROM mta.fact_delay_incidents WHERE day_type = 1
    GROUP BY month, comparison_line
), major AS (
    SELECT month, comparison_line AS line_id, sum("count") AS weekday_major_incidents
    FROM mta.fact_major_incidents WHERE day_type = 1 AND comparison_line <> ''
    GROUP BY month, comparison_line
), service AS (
    SELECT month, comparison_line AS line_id,
           sum(num_sched_trains) AS weekday_peak_sched_trains,
           sum(num_actual_trains) AS weekday_peak_actual_trains,
           100.0 * sum(num_actual_trains) / NULLIF(sum(num_sched_trains), 0) AS weekday_peak_service_delivered_percent
    FROM mta.fact_service_delivered WHERE day_type = 1
    GROUP BY month, comparison_line
)
SELECT c.*, i.weekday_delay_incidents, m.weekday_major_incidents,
       s.weekday_peak_sched_trains, s.weekday_peak_actual_trains,
       s.weekday_peak_service_delivered_percent,
       (i.line_id IS NOT NULL) AS has_incident_data,
       (m.line_id IS NOT NULL) AS has_major_incident_record,
       (s.line_id IS NOT NULL) AS has_service_data
FROM customer c
LEFT JOIN incidents i USING (month, line_id)
LEFT JOIN major m USING (month, line_id)
LEFT JOIN service s USING (month, line_id);
