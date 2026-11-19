"""Reconcile Phase 3 exports and notebook outputs with the modeled facts."""

import json
from pathlib import Path
import nbformat
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "analysis"


def main():
    customer = pd.read_csv(ROOT / "data" / "processed" / "fact_customer_journey.csv")
    annual = pd.read_csv(DATA / "annual_customer_scorecard.csv")
    priority = pd.read_csv(DATA / "06_priority_analysis.csv")
    monthly = pd.read_csv(DATA / "monthly_relationships.csv")
    relationships = json.loads((DATA / "relationship_summary.json").read_text())
    seasonality = pd.read_csv(DATA / "seasonality.csv")
    categories = pd.read_csv(DATA / "category_associations.csv")
    checks = {}
    checks["annual_customer_rows"] = len(annual) == 96 and not annual.duplicated(["line_id", "year"]).any()
    checks["annual_passenger_reconciliation"] = np.isclose(annual.passenger_trips.sum(), customer.num_passengers.sum())
    checks["annual_minutes_reconciliation"] = np.isclose(annual.net_additional_passenger_minutes.sum(), (customer.total_apt + customer.total_att).sum())
    checks["2025_scorecard_groups"] = len(priority) == 23 and priority.customer_months.eq(12).all()
    checks["2025_priority_intersection"] = set(priority.loc[(priority.reliability_rank_worst_first <= 6) & (priority.burden_rank_highest_first <= 6), "line_id"]) == {"F", "Q"}
    checks["incident_missing_not_zero"] = len(monthly[monthly.weekday_delay_incidents.isna()]) == 1 and monthly.loc[monthly.weekday_delay_incidents.isna(), "line_id"].iloc[0] == "S 42nd"
    checks["relationship_population"] = relationships["observations"] == len(monthly.dropna(subset=["weekday_delay_incidents", "cjt_percent"])) == 1101
    checks["complete_year_yoy"] = pd.isna(annual.loc[(annual.line_id == "S 42nd") & (annual.year == 2022), "cjt_change_pp"]).all()
    checks["seasonality_four_year_coverage"] = len(seasonality) == 12 and seasonality.years_observed.eq(4).all()
    checks["category_association_population"] = len(categories) == 6 and categories.line_months.eq(1101).all()
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        notebook = nbformat.read(path, as_version=4)
        outputs = [output for cell in notebook.cells if cell.cell_type == "code" for output in cell.get("outputs", [])]
        checks[f"{path.stem}_executed"] = all(cell.execution_count is not None for cell in notebook.cells if cell.cell_type == "code") and not any(output.output_type == "error" for output in outputs) and any("image/png" in output.get("data", {}) for output in outputs)
    checks = {name: bool(passed) for name, passed in checks.items()}
    result = {"passed": all(checks.values()), "checks": checks}
    (DATA / "analysis_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"{sum(checks.values())}/{len(checks)} Phase 3 checks passed")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
