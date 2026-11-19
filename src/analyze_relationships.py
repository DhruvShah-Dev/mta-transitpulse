"""Compute bounded descriptive associations and system trends from Phase 3 exports.

Run: python src/analyze_relationships.py
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "analysis"


def residualized(frame, value, dimensions):
    dummies = [pd.get_dummies(frame[column], dtype=float, drop_first=True) for column in dimensions]
    design = np.column_stack([np.ones(len(frame))] + [part.to_numpy() for part in dummies])
    observed = frame[value].to_numpy(dtype=float)
    return observed - design @ np.linalg.lstsq(design, observed, rcond=None)[0]


def correlation(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def main():
    monthly = pd.read_csv(OUT / "monthly_relationships.csv", parse_dates=["month"])
    valid = monthly.dropna(subset=["weekday_delay_incidents", "cjt_percent", "ajt_minutes_per_trip"]).copy()
    line_correlations = valid.groupby("line_id").apply(
        lambda part: pd.Series({
            "months": len(part),
            "incident_cjt_pearson": part.weekday_delay_incidents.corr(part.cjt_percent),
            "incident_ajt_pearson": part.weekday_delay_incidents.corr(part.ajt_minutes_per_trip),
        }), include_groups=False,
    ).reset_index()
    line_correlations.to_csv(OUT / "line_correlations.csv", index=False)

    same_month = {
        "observations": len(valid),
        "incident_vs_cjt_raw": correlation(valid.weekday_delay_incidents, valid.cjt_percent),
        "incident_vs_ajt_raw": correlation(valid.weekday_delay_incidents, valid.ajt_minutes_per_trip),
        "incident_vs_cjt_line_adjusted": correlation(
            residualized(valid, "weekday_delay_incidents", ["line_id"]),
            residualized(valid, "cjt_percent", ["line_id"])),
        "incident_vs_ajt_line_adjusted": correlation(
            residualized(valid, "weekday_delay_incidents", ["line_id"]),
            residualized(valid, "ajt_minutes_per_trip", ["line_id"])),
        "incident_vs_cjt_line_and_month_adjusted": correlation(
            residualized(valid, "weekday_delay_incidents", ["line_id", "month"]),
            residualized(valid, "cjt_percent", ["line_id", "month"])),
        "incident_vs_ajt_line_and_month_adjusted": correlation(
            residualized(valid, "weekday_delay_incidents", ["line_id", "month"]),
            residualized(valid, "ajt_minutes_per_trip", ["line_id", "month"])),
    }
    valid = valid.sort_values(["line_id", "month"])
    valid["next_month_cjt"] = valid.groupby("line_id").cjt_percent.shift(-1)
    valid["next_month"] = valid.groupby("line_id").month.shift(-1)
    lagged = valid[(valid.next_month - valid.month).dt.days.between(28, 31)].dropna(subset=["next_month_cjt"])
    same_month["incident_vs_next_month_cjt_line_adjusted"] = correlation(
        residualized(lagged, "weekday_delay_incidents", ["line_id"]),
        residualized(lagged, "next_month_cjt", ["line_id"]))
    same_month["lagged_observations"] = len(lagged)
    same_month["lines_with_negative_incident_cjt_correlation"] = int(line_correlations.incident_cjt_pearson.lt(0).sum())
    same_month["line_count"] = len(line_correlations)

    system = monthly.groupby("month", as_index=False).agg(
        passenger_trips=("passenger_trips", "sum"),
        over_five_trips=("over_five_trips", "sum"),
        net_additional_passenger_minutes=("net_additional_passenger_minutes", "sum"),
    )
    system["cjt_percent"] = 100 * (1 - system.over_five_trips / system.passenger_trips)
    system["ajt_minutes_per_trip"] = system.net_additional_passenger_minutes / system.passenger_trips
    system.to_csv(OUT / "monthly_system.csv", index=False)

    system["year"] = system.month.dt.year
    annual = system.groupby("year").agg(passenger_trips=("passenger_trips", "sum"), over_five_trips=("over_five_trips", "sum"))
    annual["annual_cjt_percent"] = 100 * (1 - annual.over_five_trips / annual.passenger_trips)
    system = system.merge(annual[["annual_cjt_percent"]], left_on="year", right_index=True)
    system["calendar_month"] = system.month.dt.month
    system["cjt_deviation_pp"] = system.cjt_percent - system.annual_cjt_percent
    seasonality = system.groupby("calendar_month", as_index=False).agg(
        average_cjt_deviation_pp=("cjt_deviation_pp", "mean"),
        years_observed=("year", "nunique"),
    )
    seasonality.to_csv(OUT / "seasonality.csv", index=False)

    categories = pd.read_csv(OUT / "monthly_incident_categories.csv", parse_dates=["month"])
    category_results = []
    for category, group in categories.groupby("reporting_category"):
        joined = group.merge(monthly[["month", "line_id", "cjt_percent"]], on=["month", "line_id"], how="inner", validate="one_to_one")
        category_results.append({
            "reporting_category": category,
            "line_months": len(joined),
            "weekday_incidents": int(joined.weekday_incidents.sum()),
            "incident_cjt_line_and_month_adjusted_r": correlation(
                residualized(joined, "weekday_incidents", ["line_id", "month"]),
                residualized(joined, "cjt_percent", ["line_id", "month"])),
        })
    pd.DataFrame(category_results).sort_values("incident_cjt_line_and_month_adjusted_r").to_csv(
        OUT / "category_associations.csv", index=False)

    (OUT / "relationship_summary.json").write_text(json.dumps(same_month, indent=2), encoding="utf-8")
    print(json.dumps(same_month, indent=2))


if __name__ == "__main__":
    main()
