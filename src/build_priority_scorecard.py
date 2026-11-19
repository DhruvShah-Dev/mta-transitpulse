"""Build the 2025 comparison-group priority scorecard from PostgreSQL.

Run: python src/build_priority_scorecard.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

from local_postgres import CONFIG, connection_info, is_running, start


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "analysis"
SQL = ROOT / "sql" / "analysis" / "07_priority_components.sql"
SCENARIOS = {
    "baseline": (0.40, 0.40, 0.20),
    "equal": (1 / 3, 1 / 3, 1 / 3),
    "reliability_focused": (0.60, 0.25, 0.15),
    "burden_focused": (0.25, 0.60, 0.15),
    "service_focused": (0.25, 0.25, 0.50),
}


def concern_percentile(series: pd.Series, higher_is_worse: bool) -> pd.Series:
    """Observed-rank percentile: best=0, worst=100, ties share mean rank."""
    ranks = series.rank(method="average", ascending=higher_is_worse)
    count = series.notna().sum()
    return 100 * (ranks - 1) / (count - 1) if count > 1 else ranks * 0


def competition_rank(score: pd.Series) -> pd.Series:
    return score.rank(method="min", ascending=False).astype("Int64")


def main() -> None:
    if not CONFIG.exists():
        raise RuntimeError("Run python src/local_postgres.py setup first")
    if not is_running():
        start()
    OUT.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(connection_info()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(SQL.read_text(encoding="utf-8"))
            columns = [column.name for column in cursor.description]
            source = pd.DataFrame(cursor.fetchall(), columns=columns)
    source.to_csv(OUT / "07_priority_components.csv", index=False)
    if source.line_id.duplicated().any() or not source.customer_months.eq(12).all():
        raise RuntimeError("2025 customer groups must be unique with 12 months each")

    score = source.copy()
    score["reliability_concern_score"] = concern_percentile(score.cjt_percent, False)
    score["passenger_burden_score"] = concern_percentile(score.net_additional_passenger_minutes, True)
    score["operational_risk_score"] = concern_percentile(score.service_delivered_percent, False)
    score["incident_coverage_complete"] = score.incident_months.eq(12)
    score["service_coverage_complete"] = score.service_months.eq(12)

    # Medians are empirical split points, not MTA performance targets.
    cjt_mid = score.cjt_percent.median()
    burden_mid = score.net_additional_passenger_minutes.median()
    poor = score.cjt_percent < cjt_mid
    high = score.net_additional_passenger_minutes > burden_mid
    score["priority_quadrant"] = np.select(
        [poor & high, ~poor & high, poor & ~high],
        ["High burden / Poor reliability", "High burden / Better reliability",
         "Lower burden / Poor reliability"],
        default="Lower burden / Better reliability",
    )
    # Strict Pareto dominance on the two customer outcomes. A dominated line
    # still can warrant a focused investigation; this is an unweighted check.
    score["pareto_customer_frontier"] = [
        not ((score.cjt_percent <= row.cjt_percent)
             & (score.net_additional_passenger_minutes >= row.net_additional_passenger_minutes)
             & ((score.cjt_percent < row.cjt_percent)
                | (score.net_additional_passenger_minutes > row.net_additional_passenger_minutes))).any()
        for row in score.itertuples()
    ]
    parts = ["reliability_concern_score", "passenger_burden_score", "operational_risk_score"]
    for name, weights in SCENARIOS.items():
        score[f"score_{name}"] = sum(score[part] * weight for part, weight in zip(parts, weights))
        score[f"rank_{name}"] = competition_rank(score[f"score_{name}"])
    rank_columns = [f"rank_{name}" for name in SCENARIOS]
    score["rank_best_case"] = score[rank_columns].min(axis=1)
    score["rank_worst_case"] = score[rank_columns].max(axis=1)
    score["rank_range"] = score.rank_worst_case - score.rank_best_case
    score = score.sort_values(["rank_baseline", "line_id"]).reset_index(drop=True)
    score.to_csv(OUT / "line_priority_2025.csv", index=False)
    metadata = {
        "year": 2025,
        "eligible_groups": len(score),
        "weights": {k: dict(zip(["reliability", "burden", "service"], v)) for k, v in SCENARIOS.items()},
        "quadrant_cutoffs": {"cjt_percent_median": cjt_mid,
                             "net_additional_passenger_minutes_median": burden_mid},
        "incident_coverage_incomplete": score.loc[~score.incident_coverage_complete, "line_id"].tolist(),
        "service_scoring_rule": "Raw annual ratio retained; percentile of lower ratios. Values above 100% are valid source observations.",
        "incident_scoring_rule": "Counts are diagnostic only; no commensurate all-weekday exposure denominator.",
    }
    (OUT / "priority_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"data/analysis/line_priority_2025.csv: {len(score)} comparison groups")
    print(score[["line_id", "score_baseline", "rank_baseline", "rank_best_case", "rank_worst_case"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
