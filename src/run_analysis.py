"""Run the Phase 3 SQL analysis and save small, inspectable CSV results.

Run: python src/run_analysis.py
"""

from pathlib import Path
import pandas as pd
import psycopg

from local_postgres import CONFIG, connection_info, is_running, start


ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql" / "analysis"
OUT = ROOT / "data" / "analysis"


def frame(cursor, query):
    cursor.execute(query)
    return pd.DataFrame(cursor.fetchall(), columns=[column.name for column in cursor.description])


def main():
    if not CONFIG.exists():
        raise RuntimeError("Run python src/local_postgres.py setup first")
    if not is_running():
        start()
    OUT.mkdir(exist_ok=True)
    with psycopg.connect(connection_info()) as connection:
        with connection.cursor() as cursor:
            for path in sorted(SQL.glob("*.sql")):
                result = frame(cursor, path.read_text(encoding="utf-8"))
                destination = OUT / f"{path.stem}.csv"
                result.to_csv(destination, index=False)
                print(f"{destination.relative_to(ROOT)}: {len(result)} rows")
            queries = {
                "peak_offpeak": """SELECT canonical_line AS line_id, EXTRACT(YEAR FROM month)::int AS year,
                    period, sum(num_passengers) AS passenger_trips,
                    100.0*(1-sum(over_five_mins)/sum(num_passengers)) AS cjt_percent,
                    sum(total_apt)/sum(num_passengers) AS apt_minutes_per_trip,
                    sum(total_att)/sum(num_passengers) AS att_minutes_per_trip
                    FROM mta.fact_customer_journey GROUP BY 1,2,3 ORDER BY 1,2,3""",
                "major_incident_categories": """SELECT comparison_line AS line_id,
                    EXTRACT(YEAR FROM month)::int AS year, day_type, category,
                    sum(\"count\") AS major_incidents
                    FROM mta.fact_major_incidents WHERE comparison_line <> ''
                    GROUP BY 1,2,3,4 ORDER BY 1,2,3,4""",
                "monthly_incident_categories": """SELECT month, comparison_line AS line_id,
                    reporting_category, sum(incidents) AS weekday_incidents
                    FROM mta.fact_delay_incidents
                    WHERE day_type = 1 AND reporting_category <> ''
                    GROUP BY 1,2,3 ORDER BY 1,2,3""",
                "monthly_relationships": """SELECT month, line_id, passenger_trips, total_apt_minutes,
                    total_att_minutes, net_additional_passenger_minutes,
                    over_five_trips, cjt_percent, ajt_minutes_per_trip,
                    weekday_delay_incidents, weekday_major_incidents,
                    weekday_peak_sched_trains, weekday_peak_actual_trains,
                    weekday_peak_service_delivered_percent,
                    has_incident_data, has_major_incident_record, has_service_data
                    FROM mta.mart_monthly_line_performance ORDER BY month,line_id""",
            }
            for name, query in queries.items():
                result = frame(cursor, query)
                result.to_csv(OUT / f"{name}.csv", index=False)
                print(f"data/analysis/{name}.csv: {len(result)} rows")

    reliability = pd.read_csv(OUT / "01_reliability_trends.csv")
    impact = pd.read_csv(OUT / "02_passenger_impact.csv")
    changes = pd.read_csv(OUT / "05_year_over_year.csv")
    annual = reliability.merge(impact, on=["line_id", "year"], validate="one_to_one", suffixes=("", "_impact"))
    if not (annual.passenger_trips - annual.passenger_trips_impact).abs().lt(1e-4).all():
        raise RuntimeError("Annual passenger denominators do not reconcile")
    annual = annual.drop(columns=["passenger_trips_impact", "ajt_minutes_per_trip_impact"])
    annual = annual.merge(
        changes[["line_id", "year", "cjt_change_pp", "ajt_change_minutes_per_trip"]],
        on=["line_id", "year"], how="left", validate="one_to_one",
    )
    annual.sort_values(["year", "cjt_percent", "line_id"]).to_csv(OUT / "annual_customer_scorecard.csv", index=False)
    print(f"data/analysis/annual_customer_scorecard.csv: {len(annual)} rows")


if __name__ == "__main__":
    main()
