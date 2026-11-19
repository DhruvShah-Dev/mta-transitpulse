"""Validate the Phase 5A local reporting layer and CSV mirrors."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "powerbi"
PROCESSED = ROOT / "data" / "processed"


def frame(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT / f"rpt_{name}.csv")


def close(left: float, right: float) -> bool:
    return bool(np.isclose(left, right, rtol=1e-10, atol=1e-5))


def main() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    tables = {name: pd.read_csv(OUT / f"{name}.csv") for name in manifest["tables"]}
    customer = tables["rpt_customer_month_line_period"]
    delay = tables["rpt_delay_month_line_category"]
    major = tables["rpt_major_month_line_category"]
    service = tables["rpt_service_month_line_daytype"]
    months = tables["rpt_dim_month"]
    lines = tables["rpt_dim_line"]
    priority = tables["rpt_priority_2025"]
    raw_c = pd.read_csv(PROCESSED / "fact_customer_journey.csv")
    raw_d = pd.read_csv(PROCESSED / "fact_delay_incidents.csv")
    raw_m = pd.read_csv(PROCESSED / "fact_major_incidents.csv")
    raw_s = pd.read_csv(PROCESSED / "fact_service_delivered.csv")
    checks = {}
    checks["nine_import_tables_and_hashes"] = len(tables) == 9 and all(
        len(tables[name]) == item["rows"]
        and hashlib.sha256((OUT / f"{name}.csv").read_bytes()).hexdigest() == item["sha256"]
        for name, item in manifest["tables"].items()
    )
    checks["dimension_keys_unique"] = (
        len(months) == 48 and months.month.is_unique
        and len(lines) == 23 and lines.line_id.is_unique
        and tables["rpt_dim_delay_category"].delay_category.is_unique
        and tables["rpt_dim_major_category"].major_category.is_unique
    )
    checks["fact_grains_unique"] = all([
        not customer.duplicated(["month", "line_id", "period"]).any(),
        not delay.duplicated(["month", "line_id", "day_type", "delay_category"]).any(),
        not major.duplicated(["month", "line_id", "day_type", "major_category"]).any(),
        not service.duplicated(["month", "line_id", "day_type"]).any(),
        priority.line_id.is_unique,
    ])
    checks["all_fact_keys_resolve"] = all(
        set(table.month).issubset(set(months.month)) and set(table.line_id).issubset(set(lines.line_id))
        for table in [customer, delay, major, service]
    ) and set(priority.line_id) == set(lines.line_id)
    checks["customer_reconciles_to_processed"] = all([
        close(customer.passenger_trips.sum(), raw_c.num_passengers.sum()),
        close(customer.over_five_trips.sum(), raw_c.over_five_mins.sum()),
        close(customer.platform_minutes.sum(), raw_c.total_apt.sum()),
        close(customer.train_minutes.sum(), raw_c.total_att.sum()),
    ])
    checks["operations_reconcile_to_processed"] = all([
        delay.delay_incidents.sum() == raw_d.incidents.sum(),
        major.major_incidents.sum() == raw_m.loc[raw_m.comparison_line.fillna("") != "", "count"].sum(),
        service.scheduled_peak_trains.sum() == raw_s.num_sched_trains.sum(),
        service.actual_peak_trains.sum() == raw_s.num_actual_trains.sum(),
    ])
    in_2025 = customer[customer.month.str[:4] == "2025"]
    cjt = 100 * (1 - in_2025.over_five_trips.sum() / in_2025.passenger_trips.sum())
    net = in_2025.net_additional_passenger_minutes.sum()
    checks["reported_2025_kpis"] = round(cjt, 2) == 85.40 and round(net / 1e9, 2) == 3.24
    checks["priority_matches_phase_4"] = (
        priority.sort_values("rank_baseline").head(3).line_id.tolist() == ["F", "B", "Q"]
        and priority.set_index("line_id").loc["D", "review_status"] == "Targeted reliability review"
        and priority.score_year.eq(2025).all()
        and np.allclose(priority.set_index("line_id").sort_index().score_baseline,
                        pd.read_csv(ROOT / "data" / "analysis" / "line_priority_2025.csv")
                        .set_index("line_id").sort_index().score_baseline)
    )
    checks["missing_incidents_remain_missing"] = (
        ((customer.month == "2025-04-01") & (customer.line_id == "S 42nd")).any()
        and not ((delay.month == "2025-04-01") & (delay.line_id == "S 42nd") & (delay.day_type == 1)).any()
    )
    checks["signed_and_over_100_retained"] = (
        (customer.train_minutes < 0).any()
        and (service.actual_peak_trains > service.scheduled_peak_trains).any()
        and service.rows_over_100_percent.sum() > 0
    )
    checks = {key: bool(value) for key, value in checks.items()}
    result = {"passed": all(checks.values()), "checks": checks,
              "2025_cjt_percent": cjt, "2025_net_additional_passenger_minutes": net,
              "scope": "Local PostgreSQL reporting views and exported CSVs; Power BI Desktop not yet validated"}
    (OUT / "reporting_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"{sum(checks.values())}/{len(checks)} Phase 5A reporting checks passed")
    for name, passed in checks.items():
        print(f"  {'PASS' if passed else 'FAIL'} {name}")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
