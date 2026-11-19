-- Complete-year passenger-weighted CJTP and AJT changes, in pp and minutes/trip.
WITH annual AS (
    SELECT canonical_line AS line_id, EXTRACT(YEAR FROM month)::int AS year,
           count(DISTINCT month) AS months_observed,
           sum(num_passengers) AS passenger_trips,
           100.0 * (1 - sum(over_five_mins) / NULLIF(sum(num_passengers), 0)) AS cjt_percent,
           sum(total_apt + total_att) / NULLIF(sum(num_passengers), 0) AS ajt_minutes_per_trip
    FROM mta.fact_customer_journey
    GROUP BY canonical_line, EXTRACT(YEAR FROM month)::int
    HAVING count(DISTINCT month) = 12
)
SELECT *, cjt_percent - lag(cjt_percent) OVER (PARTITION BY line_id ORDER BY year) AS cjt_change_pp,
          ajt_minutes_per_trip - lag(ajt_minutes_per_trip) OVER (PARTITION BY line_id ORDER BY year) AS ajt_change_minutes_per_trip
FROM annual
ORDER BY line_id, year;
