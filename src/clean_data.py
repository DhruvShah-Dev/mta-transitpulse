"""Create lossless, typed MTA fact CSVs from the 2022-2025 raw snapshot.

Run: python src/clean_data.py
"""

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
MAPPING = ROOT / "docs" / "line_mapping.csv"
FILES = {
    "customer_journey": "subway_customer_journey.csv",
    "delay_incidents": "subway_delay_incidents.csv",
    "major_incidents": "subway_major_incidents.csv",
    "service_delivered": "subway_service_delivered.csv",
}
SCHEMAS = {
    "customer_journey": ["month", "division", "line", "period", "num_passengers", "additional_platform_time", "additional_train_time", "total_apt", "total_att", "over_five_mins", "over_five_mins_perc", "customer_journey_time"],
    "delay_incidents": ["month", "division", "line", "day_type", "reporting_category", "incidents"],
    "major_incidents": ["month", "division", "line", "day_type", "category", "count"],
    "service_delivered": ["month", "division", "line", "day_type", "num_sched_trains", "num_actual_trains", "service_delivered"],
}
KEYS = {
    "customer_journey": ["month", "division", "line", "period"],
    "delay_incidents": ["month", "division", "line", "day_type", "reporting_category"],
    "major_incidents": ["month", "division", "line", "day_type", "category"],
    "service_delivered": ["month", "division", "line", "day_type"],
}


def load_mapping():
    mapping = pd.read_csv(MAPPING, keep_default_na=False, dtype=str)
    if mapping.duplicated(["source_dataset", "original_line"]).any():
        raise ValueError("Duplicate source line mapping")
    return mapping


def clean(source, mapping):
    frame = pd.read_csv(RAW / FILES[source], keep_default_na=False, dtype=str)
    if list(frame.columns) != SCHEMAS[source]:
        raise ValueError(f"Unexpected {source} columns: {list(frame.columns)}")
    frame.insert(0, "source_row_id", range(1, len(frame) + 1))
    month = pd.to_datetime(frame["month"], errors="raise")
    if not month.dt.is_month_start.all() or not month.between("2022-01-01", "2025-12-01").all():
        raise ValueError(f"Invalid reporting month in {source}")
    frame["month"] = month.dt.strftime("%Y-%m-%d")
    frame["line"] = frame["line"].str.strip()
    if frame.duplicated(KEYS[source]).any():
        raise ValueError(f"Duplicate raw grain in {source}")
    own_map = mapping.loc[mapping.source_dataset.eq(source), ["original_line", "canonical_line", "comparison_line", "mapping_status"]]
    frame = frame.merge(own_map, left_on="line", right_on="original_line", how="left", validate="many_to_one", sort=False)
    if frame.canonical_line.isna().any():
        raise ValueError(f"Unmapped lines in {source}: {frame.loc[frame.canonical_line.isna(), 'line'].unique().tolist()}")
    frame.drop(columns="original_line", inplace=True)
    for col in frame.columns:
        if col in {"source_row_id", "month", "division", "line", "period", "reporting_category", "category", "canonical_line", "comparison_line", "mapping_status"}:
            continue
        frame[col] = pd.to_numeric(frame[col], errors="raise")
    if source == "customer_journey":
        frame["ajt_minutes_per_trip"] = frame.additional_platform_time + frame.additional_train_time
        frame["net_additional_passenger_minutes"] = frame.total_apt + frame.total_att
        frame["cjt_percent"] = 100 * frame.customer_journey_time
        frame["over_five_percent"] = 100 * frame.over_five_mins_perc
    elif source == "delay_incidents":
        frame["category_status"] = frame.reporting_category.apply(lambda x: "uncategorized_zero" if x == "" else "categorized")
    elif source == "service_delivered":
        frame["service_delivered_percent"] = 100 * frame.num_actual_trains / frame.num_sched_trains
    frame.sort_values("source_row_id", inplace=True)
    if len(frame) != sum(1 for _ in open(RAW / FILES[source], encoding="utf-8")) - 1:
        raise ValueError(f"Row count changed during mapping: {source}")
    return frame


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mapping = load_mapping()
    for source in FILES:
        frame = clean(source, mapping)
        path = OUT / f"fact_{source}.csv"
        frame.to_csv(path, index=False, float_format="%.15g")
        print(f"{path.relative_to(ROOT)}: {len(frame):,} rows")


if __name__ == "__main__":
    main()
