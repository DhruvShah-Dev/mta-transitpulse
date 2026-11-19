"""Load validated fact CSVs into PostgreSQL.

Set MTA_DATABASE_URL or standard PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD.
Run from project root: python src/load_postgres.py
"""

import os
from pathlib import Path
import psycopg

from validate_data import main as validate
from local_postgres import CONFIG, connection_info, is_running, start


ROOT = Path(__file__).resolve().parents[1]


def main():
    validate()
    if os.environ.get("MTA_DATABASE_URL"):
        conninfo = os.environ["MTA_DATABASE_URL"]
    elif any(os.environ.get(key) for key in ("PGHOST", "PGDATABASE", "PGUSER", "PGSERVICE")):
        conninfo = ""
    elif CONFIG.exists():
        if not is_running():
            start()
        conninfo = connection_info()
    else:
        conninfo = "dbname=postgres"
    with psycopg.connect(conninfo) as connection:
        with connection.cursor() as cursor:
            cursor.execute((ROOT / "sql" / "01_create_schema.sql").read_text(encoding="utf-8"))
            cursor.execute("""TRUNCATE mta.fact_customer_journey, mta.fact_delay_incidents,
                mta.fact_major_incidents, mta.fact_service_delivered,
                mta.dim_incident_category, mta.line_mapping, mta.dim_subway_line,
                mta.dim_calendar_month, mta.dim_reporting_period CASCADE""")
            cursor.execute("""INSERT INTO mta.dim_calendar_month
                SELECT generate_series('2022-01-01'::date, '2025-12-01'::date, interval '1 month')::date""")
            cursor.execute("""INSERT INTO mta.dim_reporting_period VALUES
                ('peak', 'Customer journey weekday 7-10 AM and 4-7 PM'),
                ('offpeak', 'Customer journey weekday 6-7 AM, 10 AM-4 PM, and 7-11 PM')""")

            def copy_csv(table, file):
                command = f"COPY mta.{table} FROM STDIN WITH (FORMAT csv, HEADER true, NULL '\\N')"
                with cursor.copy(command) as copier, (ROOT / file).open("rb") as source:
                    while chunk := source.read(1024 * 1024):
                        copier.write(chunk)

            copy_csv("line_mapping", "docs/line_mapping.csv")
            cursor.execute("""INSERT INTO mta.dim_subway_line
                SELECT canonical_line FROM mta.line_mapping
                UNION SELECT comparison_line FROM mta.line_mapping WHERE comparison_line <> ''""")
            for table in ["fact_customer_journey", "fact_delay_incidents", "fact_major_incidents", "fact_service_delivered"]:
                copy_csv(table, f"data/processed/{table}.csv")
            cursor.execute("""INSERT INTO mta.dim_incident_category
                SELECT DISTINCT 'delay_incidents', reporting_category FROM mta.fact_delay_incidents
                UNION SELECT DISTINCT 'major_incidents', category FROM mta.fact_major_incidents""")
            cursor.execute((ROOT / "sql" / "04_monthly_performance.sql").read_text(encoding="utf-8"))
            cursor.execute((ROOT / "sql" / "03_quality_checks.sql").read_text(encoding="utf-8"))
            failures = cursor.fetchall()
            cursor.execute("SELECT count(*) FROM mta.mart_monthly_line_performance")
            mart_rows = cursor.fetchone()[0]
    if failures:
        raise RuntimeError(f"SQL reconciliation failed: {failures}")
    print(f"PostgreSQL load complete; {mart_rows} monthly comparison rows; SQL checks passed")


if __name__ == "__main__":
    main()
