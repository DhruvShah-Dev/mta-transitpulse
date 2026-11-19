-- Return zero rows for failures. Missing major-event rows remain NULL in the mart.
WITH counts AS (
 SELECT 'customer_rows' AS check_name, count(*)::numeric AS actual, 2300::numeric AS expected FROM mta.fact_customer_journey
 UNION ALL SELECT 'incident_rows', count(*), 15043 FROM mta.fact_delay_incidents
 UNION ALL SELECT 'major_rows', count(*), 1920 FROM mta.fact_major_incidents
 UNION ALL SELECT 'service_rows', count(*), 2212 FROM mta.fact_service_delivered
 UNION ALL SELECT 'mart_unique_keys', count(*) - count(DISTINCT (month, line_id)), 0 FROM mta.mart_monthly_line_performance
 UNION ALL SELECT 'mart_passenger_reconciliation', abs((SELECT sum(passenger_trips) FROM mta.mart_monthly_line_performance) - (SELECT sum(num_passengers) FROM mta.fact_customer_journey)), 0
 UNION ALL SELECT 'mart_minutes_reconciliation', abs((SELECT sum(net_additional_passenger_minutes) FROM mta.mart_monthly_line_performance) - (SELECT sum(total_apt + total_att) FROM mta.fact_customer_journey)), 0
 UNION ALL SELECT 'invalid_customer_percent', count(*), 0 FROM mta.fact_customer_journey WHERE cjt_percent NOT BETWEEN 0 AND 100
 UNION ALL SELECT 'negative_incidents', count(*), 0 FROM mta.fact_delay_incidents WHERE incidents < 0
)
SELECT * FROM counts WHERE abs(actual - expected) > 0.0001;
