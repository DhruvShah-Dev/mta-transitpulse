-- Run with psql from the project root: psql -v ON_ERROR_STOP=1 -d DATABASE -f sql/02_load_data.sql
\set ON_ERROR_STOP on
BEGIN;
TRUNCATE mta.fact_customer_journey, mta.fact_delay_incidents, mta.fact_major_incidents,
         mta.fact_service_delivered, mta.dim_incident_category, mta.line_mapping,
         mta.dim_subway_line, mta.dim_calendar_month, mta.dim_reporting_period CASCADE;
INSERT INTO mta.dim_calendar_month
SELECT generate_series('2022-01-01'::date, '2025-12-01'::date, interval '1 month')::date;
INSERT INTO mta.dim_reporting_period VALUES
  ('peak', 'Customer journey weekday 7-10 AM and 4-7 PM'),
  ('offpeak', 'Customer journey weekday 6-7 AM, 10 AM-4 PM, and 7-11 PM');
\copy mta.line_mapping FROM 'docs/line_mapping.csv' WITH (FORMAT csv, HEADER true, NULL '\N')
INSERT INTO mta.dim_subway_line
SELECT canonical_line FROM mta.line_mapping
UNION SELECT comparison_line FROM mta.line_mapping WHERE comparison_line <> '';
\copy mta.fact_customer_journey FROM 'data/processed/fact_customer_journey.csv' WITH (FORMAT csv, HEADER true, NULL '\N')
\copy mta.fact_delay_incidents FROM 'data/processed/fact_delay_incidents.csv' WITH (FORMAT csv, HEADER true, NULL '\N')
\copy mta.fact_major_incidents FROM 'data/processed/fact_major_incidents.csv' WITH (FORMAT csv, HEADER true, NULL '\N')
\copy mta.fact_service_delivered FROM 'data/processed/fact_service_delivered.csv' WITH (FORMAT csv, HEADER true, NULL '\N')
INSERT INTO mta.dim_incident_category
SELECT DISTINCT 'delay_incidents', reporting_category FROM mta.fact_delay_incidents
UNION SELECT DISTINCT 'major_incidents', category FROM mta.fact_major_incidents;
COMMIT;
