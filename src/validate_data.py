"""Validate source-to-clean reconciliation and the planned monthly joins.

Run: python src/validate_data.py
Writes data/validation/validation_report.json and exits nonzero on failure.
"""

import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

from clean_data import FILES, KEYS, RAW, ROOT, SCHEMAS, clean, load_mapping


OUT = ROOT / "data" / "processed"
REPORT = ROOT / "data" / "validation" / "validation_report.json"


def close(a, b, rtol=1e-10, atol=1e-5):
    return bool(np.allclose(a, b, rtol=rtol, atol=atol, equal_nan=False))


def main():
    manifest = json.loads((ROOT / "data" / "source_manifest.json").read_text(encoding="utf-8"))
    expected = {row["id"]: row for row in manifest["datasets"]}
    ids = dict(zip(FILES, ["r7qk-6tcy", "g937-7k7c", "ereg-mcvp", "32ch-sei3"]))
    mapping = load_mapping()
    checks = []

    def record(name, passed, detail):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    facts = {}
    for source, filename in FILES.items():
        raw_path = RAW / filename
        raw = pd.read_csv(raw_path, keep_default_na=False, dtype=str)
        fact = pd.read_csv(OUT / f"fact_{source}.csv", keep_default_na=False)
        facts[source] = fact
        digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        record(f"{source}: raw SHA-256", digest == expected[ids[source]]["sha256"], digest)
        record(f"{source}: schema", list(raw.columns) == SCHEMAS[source], list(raw.columns))
        record(f"{source}: row count", len(raw) == len(fact) == expected[ids[source]]["rows"], f"raw={len(raw)} cleaned={len(fact)}")
        record(f"{source}: 48 target months", raw.month.nunique() == 48 and raw.month.min().startswith("2022-01") and raw.month.max().startswith("2025-12"), f"{raw.month.min()[:10]} to {raw.month.max()[:10]}")
        record(f"{source}: unique raw grain", not raw.duplicated(KEYS[source]).any(), int(raw.duplicated(KEYS[source]).sum()))
        record(f"{source}: clean source-row IDs", fact.source_row_id.tolist() == list(range(1, len(raw) + 1)), len(fact))
        record(f"{source}: mapped lines", fact.canonical_line.notna().all() and fact.mapping_status.notna().all(), sorted(fact.canonical_line.unique().tolist()))
        record(f"{source}: deterministic clean rebuild", fact.shape == clean(source, mapping).shape, list(fact.columns))
        record(f"{source}: numeric date range", fact.month.min() == "2022-01-01" and fact.month.max() == "2025-12-01", f"{fact.month.min()} to {fact.month.max()}")

    c = facts["customer_journey"]
    d = facts["delay_incidents"]
    m = facts["major_incidents"]
    s = facts["service_delivered"]
    record("all raw records retained", sum(len(x) for x in facts.values()) == 21475, sum(len(x) for x in facts.values()))
    record("customer percentages and identities", close(c.cjt_percent, 100 * (1 - c.over_five_mins_perc)) and close(c.total_apt, c.num_passengers * c.additional_platform_time) and close(c.total_att, c.num_passengers * c.additional_train_time), "weighted fields reconcile")
    record("customer percentage bounds", c.cjt_percent.between(0, 100).all() and c.over_five_percent.between(0, 100).all(), f"CJTP {c.cjt_percent.min():.3f} to {c.cjt_percent.max():.3f}%")
    record("incident counts and blank category", d.incidents.ge(0).all() and d.loc[d.reporting_category.eq(""), "incidents"].eq(0).all(), f"blank categories={int(d.reporting_category.eq('').sum())}")
    record("major counts and unassigned lines", m["count"].ge(0).all() and int(m.line.eq("").sum()) == 8 and m.loc[m.line.eq(""), "comparison_line"].eq("").all(), f"unassigned={int(m.line.eq('').sum())}")
    record("service count ratio and source scale", s.num_sched_trains.gt(0).all() and s.num_actual_trains.ge(0).all() and close(s.service_delivered_percent, 100 * s.num_actual_trains / s.num_sched_trains) and close(s.service_delivered, s.num_actual_trains / s.num_sched_trains / 100, atol=1e-10), "raw = count ratio / 100")
    record("service percentage nonnegative", s.service_delivered_percent.ge(0).all(), f"{s.service_delivered_percent.min():.3f} to {s.service_delivered_percent.max():.3f}%")
    record("N/W source mapping", d.loc[d.line.eq("N"), "comparison_line"].eq("NW").all() and m.loc[m.line.eq("N"), "comparison_line"].eq("NW").all() and c.loc[c.line.isin(["N", "W"]), "comparison_line"].eq("NW").all(), "N+W only at comparison grain")
    record("shuttle alias mapping", all(s.loc[s.line.eq(k), "canonical_line"].eq(v).all() for k, v in {"FS": "S Fkln", "GS": "S 42nd", "H": "S Rock"}.items()), "MTA GTFS route IDs")

    def aggregate(frame, value, name):
        return frame.groupby(["month", "comparison_line"], as_index=False)[value].sum().rename(columns={value: name})

    customer = c.groupby(["month", "comparison_line"], as_index=False).agg(
        passenger_trips=("num_passengers", "sum"),
        net_minutes=("net_additional_passenger_minutes", "sum"),
        over_five_trips=("over_five_mins", "sum"),
    )
    incident = aggregate(d[d.day_type.eq(1)], "incidents", "weekday_incidents")
    major = aggregate(m[m.day_type.eq(1) & m.comparison_line.ne("")], "count", "weekday_major")
    service = s[s.day_type.eq(1)].groupby(["month", "comparison_line"], as_index=False).agg(scheduled=("num_sched_trains", "sum"), actual=("num_actual_trains", "sum"))
    mart = customer.merge(incident, on=["month", "comparison_line"], how="left", validate="one_to_one")
    mart = mart.merge(major, on=["month", "comparison_line"], how="left", validate="one_to_one")
    mart = mart.merge(service, on=["month", "comparison_line"], how="left", validate="one_to_one")
    record("mart unique keys and no row multiplication", len(mart) == len(customer) and not mart.duplicated(["month", "comparison_line"]).any(), f"{len(mart)} line-months")
    record("mart passenger and minute reconciliation", close(mart.passenger_trips.sum(), c.num_passengers.sum()) and close(mart.net_minutes.sum(), c.net_additional_passenger_minutes.sum()), "source totals equal mart totals")
    missing_incidents = mart.loc[mart.weekday_incidents.isna(), ["month", "comparison_line"]].to_dict("records")
    record("incident join exception preserved", missing_incidents == [{"month": "2025-04-01", "comparison_line": "S 42nd"}], missing_incidents)
    record("service join coverage", mart.scheduled.notna().all(), f"missing={int(mart.scheduled.isna().sum())}")
    record("major-event missing kept distinct", mart.weekday_major.isna().any(), f"no record={int(mart.weekday_major.isna().sum())}")
    record("incident and service source totals unchanged", close(incident.weekday_incidents.sum(), d.loc[d.day_type.eq(1), "incidents"].sum()) and close(service.scheduled.sum(), s.loc[s.day_type.eq(1), "num_sched_trains"].sum()), "detail sums reconcile before join")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "passed": all(x["passed"] for x in checks),
        "check_count": len(checks),
        "failed_count": sum(not x["passed"] for x in checks),
        "source_exceptions": {
            "service_delivered_over_100_percent_rows": int(s.service_delivered_percent.gt(100).sum()),
            "service_delivered_max_percent": float(s.service_delivered_percent.max()),
            "customer_line_months_without_weekday_incident_row": missing_incidents,
            "major_event_unassigned_line_rows": int(m.line.eq("").sum()),
        },
        "checks": checks,
    }
    REPORT.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"{sum(x['passed'] for x in checks)}/{len(checks)} checks passed; report: {REPORT.relative_to(ROOT)}")
    for row in checks:
        if not row["passed"]:
            print("FAILED:", row["check"], row["detail"])
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
