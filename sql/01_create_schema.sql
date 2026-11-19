CREATE SCHEMA IF NOT EXISTS mta;

CREATE TABLE IF NOT EXISTS mta.dim_calendar_month (
    month date PRIMARY KEY CHECK (EXTRACT(DAY FROM month) = 1)
);
CREATE TABLE IF NOT EXISTS mta.dim_subway_line (
    line_id text PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS mta.dim_reporting_period (
    period_code text PRIMARY KEY,
    definition text NOT NULL
);
CREATE TABLE IF NOT EXISTS mta.dim_incident_category (
    source_dataset text NOT NULL,
    category text NOT NULL,
    PRIMARY KEY (source_dataset, category)
);
CREATE TABLE IF NOT EXISTS mta.line_mapping (
    source_dataset text NOT NULL,
    original_line text NOT NULL,
    canonical_line text NOT NULL,
    comparison_line text NOT NULL,
    mapping_status text NOT NULL,
    evidence text NOT NULL,
    PRIMARY KEY (source_dataset, original_line)
);

CREATE TABLE IF NOT EXISTS mta.fact_customer_journey (
    source_row_id bigint PRIMARY KEY,
    month date NOT NULL REFERENCES mta.dim_calendar_month,
    division text NOT NULL,
    line text NOT NULL,
    period text NOT NULL REFERENCES mta.dim_reporting_period(period_code),
    num_passengers double precision NOT NULL,
    additional_platform_time double precision NOT NULL,
    additional_train_time double precision NOT NULL,
    total_apt double precision NOT NULL,
    total_att double precision NOT NULL,
    over_five_mins double precision NOT NULL,
    over_five_mins_perc double precision NOT NULL,
    customer_journey_time double precision NOT NULL,
    canonical_line text NOT NULL REFERENCES mta.dim_subway_line,
    comparison_line text NOT NULL REFERENCES mta.dim_subway_line,
    mapping_status text NOT NULL,
    ajt_minutes_per_trip double precision NOT NULL,
    net_additional_passenger_minutes double precision NOT NULL,
    cjt_percent double precision NOT NULL CHECK (cjt_percent BETWEEN 0 AND 100),
    over_five_percent double precision NOT NULL CHECK (over_five_percent BETWEEN 0 AND 100),
    UNIQUE (month, division, line, period)
);
CREATE TABLE IF NOT EXISTS mta.fact_delay_incidents (
    source_row_id bigint PRIMARY KEY,
    month date NOT NULL REFERENCES mta.dim_calendar_month,
    division text NOT NULL,
    line text NOT NULL,
    day_type smallint NOT NULL CHECK (day_type IN (1,2)),
    reporting_category text NOT NULL,
    incidents integer NOT NULL CHECK (incidents >= 0),
    canonical_line text NOT NULL REFERENCES mta.dim_subway_line,
    comparison_line text NOT NULL REFERENCES mta.dim_subway_line,
    mapping_status text NOT NULL,
    category_status text NOT NULL,
    UNIQUE (month, division, line, day_type, reporting_category)
);
CREATE TABLE IF NOT EXISTS mta.fact_major_incidents (
    source_row_id bigint PRIMARY KEY,
    month date NOT NULL REFERENCES mta.dim_calendar_month,
    division text NOT NULL,
    line text NOT NULL,
    day_type smallint NOT NULL CHECK (day_type IN (1,2)),
    category text NOT NULL,
    "count" integer NOT NULL CHECK ("count" >= 0),
    canonical_line text NOT NULL REFERENCES mta.dim_subway_line,
    comparison_line text NOT NULL,
    mapping_status text NOT NULL,
    UNIQUE (month, division, line, day_type, category)
);
CREATE TABLE IF NOT EXISTS mta.fact_service_delivered (
    source_row_id bigint PRIMARY KEY,
    month date NOT NULL REFERENCES mta.dim_calendar_month,
    division text NOT NULL,
    line text NOT NULL,
    day_type smallint NOT NULL CHECK (day_type IN (1,2)),
    num_sched_trains integer NOT NULL CHECK (num_sched_trains > 0),
    num_actual_trains integer NOT NULL CHECK (num_actual_trains >= 0),
    service_delivered double precision NOT NULL,
    canonical_line text NOT NULL REFERENCES mta.dim_subway_line,
    comparison_line text NOT NULL REFERENCES mta.dim_subway_line,
    mapping_status text NOT NULL,
    service_delivered_percent double precision NOT NULL CHECK (service_delivered_percent >= 0),
    UNIQUE (month, division, line, day_type)
);
