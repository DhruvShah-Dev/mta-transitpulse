"""Create PostgreSQL Power BI views, load fixed 2025 priorities, and export CSVs.

Run: python src/build_powerbi_reporting.py
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg
from psycopg import sql

from local_postgres import CONFIG, connection_info, is_running, start


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "powerbi"
VIEWS = [
    "rpt_dim_month", "rpt_dim_line", "rpt_dim_delay_category", "rpt_dim_major_category",
    "rpt_customer_month_line_period", "rpt_delay_month_line_category",
    "rpt_major_month_line_category", "rpt_service_month_line_daytype", "rpt_priority_2025",
]


def load_priority(cursor: psycopg.Cursor) -> None:
    path = ROOT / "data" / "analysis" / "line_priority_2025.csv"
    frame = pd.read_csv(path)
    frame["score_year"] = 2025
    frame["review_status"] = np.select(
        [frame.line_id.isin(["F", "B", "Q"]), frame.line_id.eq("D")],
        ["First investigation", "Targeted reliability review"],
        default="Monitor / diagnose",
    )
    if frame.line_id.duplicated().any() or len(frame) != 23:
        raise RuntimeError("Priority input must have 23 unique groups")
    type_map = {"i": "bigint", "u": "bigint", "f": "double precision", "b": "boolean"}
    definitions = [
        sql.SQL("{} {}").format(sql.Identifier(column), sql.SQL(type_map.get(frame[column].dtype.kind, "text")))
        for column in frame.columns
    ]
    cursor.execute("DROP TABLE IF EXISTS mta.rpt_priority_2025")
    cursor.execute(sql.SQL("CREATE TABLE mta.rpt_priority_2025 ({}, PRIMARY KEY (line_id))").format(sql.SQL(", ").join(definitions)))
    copy_columns = sql.SQL(", ").join(map(sql.Identifier, frame.columns))
    command = sql.SQL("COPY mta.rpt_priority_2025 ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)").format(copy_columns)
    with cursor.copy(command) as copy:
        copy.write(frame.to_csv(index=False, na_rep="").encode("utf-8"))


def read_frame(cursor: psycopg.Cursor, query: str) -> pd.DataFrame:
    cursor.execute(query)
    return pd.DataFrame(cursor.fetchall(), columns=[column.name for column in cursor.description])


def main() -> None:
    if not CONFIG.exists():
        raise RuntimeError("Run python src/local_postgres.py setup first")
    if not is_running():
        start()
    OUT.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(connection_info()) as connection:
        with connection.cursor() as cursor:
            cursor.execute((ROOT / "sql" / "05_powerbi_reporting.sql").read_text(encoding="utf-8"))
            load_priority(cursor)
            records = {}
            for name in VIEWS:
                path = OUT / f"{name}.csv"
                data = read_frame(cursor, f"SELECT * FROM mta.{name} ORDER BY 1")
                data.to_csv(path, index=False)
                records[name] = {"rows": len(data), "columns": list(data.columns),
                                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                print(f"{path.relative_to(ROOT)}: {len(data)} rows")
            customer = pd.read_csv(OUT / "rpt_customer_month_line_period.csv", parse_dates=["month"])
            priority = pd.read_csv(OUT / "rpt_priority_2025.csv")
            selected = customer[customer.month.dt.year == 2025]
            cjt_2025 = 100 * (1 - selected.over_five_trips.sum() / selected.passenger_trips.sum())
            net_2025 = selected.net_additional_passenger_minutes.sum()
            original = pd.read_csv(ROOT / "data" / "analysis" / "line_priority_2025.csv")
            if round(cjt_2025, 2) != 85.40 or round(net_2025 / 1e9, 2) != 3.24:
                raise RuntimeError(f"2025 KPI reconciliation failed: CJTP={cjt_2025}, net={net_2025}")
            # Exact CSV roundtrips can alter floating-point representation.
            left, right = priority.set_index("line_id"), original.set_index("line_id")
            if set(left.index) != set(right.index) or any(
                not (np.allclose(left[col].sort_index(), right[col].sort_index(), equal_nan=True)
                     if pd.api.types.is_numeric_dtype(right[col]) else left[col].sort_index().equals(right[col].sort_index()))
                for col in right.columns
            ):
                raise RuntimeError("PostgreSQL priority table differs from Phase 4 CSV")
            if priority.nsmallest(3, "rank_baseline").line_id.tolist() != ["F", "B", "Q"]:
                raise RuntimeError("Priority order differs from Phase 4")
            manifest = {"source_period": "2022-01 through 2025-12", "mode": "PostgreSQL views with CSV mirror",
                        "2025_cjt_percent": cjt_2025, "2025_net_additional_passenger_minutes": net_2025,
                        "tables": records}
            (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"2025 CJTP {cjt_2025:.4f}%; net additional time {net_2025/1e9:.4f}B minutes")


if __name__ == "__main__":
    main()
