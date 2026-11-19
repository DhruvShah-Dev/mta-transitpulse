"""Seven Phase 4 checks against exported inputs, scores, and notebook."""

import json
from pathlib import Path

import nbformat
import numpy as np
import pandas as pd

from build_priority_scorecard import SCENARIOS, concern_percentile


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "analysis"


def main() -> None:
    inputs = pd.read_csv(DATA / "07_priority_components.csv")
    score = pd.read_csv(DATA / "line_priority_2025.csv")
    prior = pd.read_csv(DATA / "06_priority_analysis.csv")
    meta = json.loads((DATA / "priority_metadata.json").read_text(encoding="utf-8"))
    method = (ROOT / "reports" / "PRIORITIZATION_METHOD.md").read_text(encoding="utf-8")
    recommendations = (ROOT / "reports" / "PRIORITY_RECOMMENDATIONS.md").read_text(encoding="utf-8")
    checks = {}
    checks["one_row_per_eligible_group"] = (
        len(score) == len(inputs) == len(prior) == 23
        and score.line_id.is_unique and inputs.line_id.is_unique
        and set(score.line_id) == set(prior.line_id)
        and score.customer_months.eq(12).all()
    )
    units = ["percent", "minutes", "trip", "count", "signed", "peak", "weight"]
    checks["inputs_documented_and_reconciled"] = (
        all(word in method.lower() for word in units)
        and np.allclose(score.cjt_percent, 100 * (1 - score.trips_over_five_minutes / score.passenger_trips))
        and np.allclose(score.net_additional_passenger_minutes, score.platform_minutes + score.train_minutes)
        and np.allclose(score.ajt_minutes_per_trip, score.net_additional_passenger_minutes / score.passenger_trips)
        and np.allclose(score.service_delivered_percent, 100 * score.actual_peak_trains / score.scheduled_peak_trains)
        and np.allclose(score.cjt_percent, prior.set_index("line_id").loc[score.line_id, "cjt_percent"])
        and np.allclose(score.net_additional_passenger_minutes,
                        prior.set_index("line_id").loc[score.line_id, "net_additional_passenger_minutes"])
    )
    shuttle = score.set_index("line_id").loc["S 42nd"]
    checks["missing_distinct_from_zero"] = (
        shuttle.incident_months == 11 and shuttle.weekday_delay_incidents > 0
        and np.isnan(shuttle.cjt_2022_percent)
        and score.loc[score.line_id == "S Rock", "weekday_major_incidents"].isna().all()
        and meta["incident_coverage_incomplete"] == ["S 42nd"]
    )
    parts = ["reliability_concern_score", "passenger_burden_score", "operational_risk_score"]
    checks["components_bounded"] = score[parts].notna().all().all() and score[parts].ge(0).all().all() and score[parts].le(100).all().all()
    recalculated = [
        concern_percentile(score.cjt_percent, False),
        concern_percentile(score.net_additional_passenger_minutes, True),
        concern_percentile(score.service_delivered_percent, False),
    ]
    checks["weights_reproduce_ranks"] = all(
        np.allclose(score[part], expected) for part, expected in zip(parts, recalculated)
    ) and all(
        np.allclose(score[f"score_{name}"], sum(score[part] * weight for part, weight in zip(parts, weights)))
        and score[f"rank_{name}"].equals(score[f"score_{name}"].rank(method="min", ascending=False).astype(int))
        for name, weights in SCENARIOS.items()
    ) and score[[f"rank_{name}" for name in SCENARIOS]].nunique(axis=1).gt(1).any()
    focus = score.set_index("line_id").loc[["F", "Q", "B", "D"]]
    checks["four_lines_compared"] = (
        len(focus) == 4 and focus.cjt_percent.notna().all()
        and focus.net_additional_passenger_minutes.notna().all()
        and all(f"| {line} |" in recommendations for line in ["F", "Q", "B", "D"])
    )
    notebook = nbformat.read(ROOT / "notebooks" / "03_priority_analysis.ipynb", as_version=4)
    code = [cell for cell in notebook.cells if cell.cell_type == "code"]
    outputs = [output for cell in code for output in cell.outputs]
    checks["recommendations_and_visual_evidence"] = (
        all(term in recommendations.lower() for term in ["investigat", "limits", "weight", "incident", "service", "f", "q", "b", "d"])
        and all(cell.execution_count is not None for cell in code)
        and not any(output.output_type == "error" for output in outputs)
        and sum("image/png" in output.get("data", {}) for output in outputs) >= 3
    )
    checks = {name: bool(passed) for name, passed in checks.items()}
    result = {"passed": all(checks.values()), "checks": checks}
    (DATA / "priority_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"{sum(checks.values())}/{len(checks)} Phase 4 checks passed")
    for name, passed in checks.items():
        print(f"  {'PASS' if passed else 'FAIL'} {name}")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
