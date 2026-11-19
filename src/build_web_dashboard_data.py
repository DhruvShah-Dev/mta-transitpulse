"""Build the fixed, source-backed snapshot for the public TransitPulse dashboard."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "web" / "dashboard_snapshot.json"
APP_DATA = ROOT / "dashboards" / "transitpulse-web" / "src" / "data.json"


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def number(value: str | None) -> float:
    return float(value or 0)


def source(label: str, files: list[str], definition: str, formula: str = "") -> dict:
    metric = {"label": label, "definition": definition, "sourceLineage": [{"files": files}]}
    if formula:
        metric["formula"] = formula
    return {
        "label": "MTA Open Data; validated TransitPulse snapshot",
        "files": files,
        "links": [
            {"label": "Customer Journey-Focused Metrics", "url": "https://data.ny.gov/d/r7qk-6tcy"},
            {"label": "Delay-Causing Incidents", "url": "https://data.ny.gov/d/g937-7k7c"},
            {"label": "Service Delivered", "url": "https://data.ny.gov/d/32ch-sei3"},
        ],
        "filters": ["January 2022–December 2025; historical snapshot retrieved 19 November 2026"],
        "metricDefinitions": [metric],
    }


def build() -> dict:
    monthly_input = read_csv("data/analysis/monthly_system.csv")
    monthly = []
    annual_totals = defaultdict(lambda: defaultdict(float))
    for row in monthly_input:
        year = int(row["month"][:4])
        trips = number(row["passenger_trips"])
        late = number(row["over_five_trips"])
        minutes = number(row["net_additional_passenger_minutes"])
        monthly.append({
            "month": row["month"], "year": year, "passengerTrips": trips,
            "lateTrips": late, "netMinutes": minutes,
            "cjtPercent": 100 * (1 - late / trips),
            "ajtMinutes": minutes / trips,
        })
        for key, value in (("passengerTrips", trips), ("lateTrips", late), ("netMinutes", minutes)):
            annual_totals[year][key] += value

    annual = []
    for year in sorted(annual_totals):
        totals = annual_totals[year]
        annual.append({
            "year": str(year), "passengerTrips": totals["passengerTrips"],
            "lateTrips": totals["lateTrips"], "netMinutes": totals["netMinutes"],
            "cjtPercent": 100 * (1 - totals["lateTrips"] / totals["passengerTrips"]),
            "ajtMinutes": totals["netMinutes"] / totals["passengerTrips"],
        })

    priority = []
    history = []
    for row in read_csv("data/analysis/line_priority_2025.csv"):
        line = row["line_id"]
        priority.append({
            "line": line, "cjtPercent": number(row["cjt_percent"]),
            "netMinutesM": number(row["net_additional_passenger_minutes"]) / 1_000_000,
            "ajtMinutes": number(row["ajt_minutes_per_trip"]),
            "delayIncidents": int(number(row["weekday_delay_incidents"])),
            "servicePercent": number(row["service_delivered_percent"]),
            "score": number(row["score_baseline"]),
            "rank": int(row["rank_baseline"]),
            "rankBest": int(row["rank_best_case"]),
            "rankWorst": int(row["rank_worst_case"]),
            "quadrant": row["priority_quadrant"],
            "incidentMonths": int(number(row["incident_months"])),
            "serviceMonths": int(number(row["service_months"])),
        })
        for year in range(2022, 2026):
            value = row["cjt_percent"] if year == 2025 else row[f"cjt_{year}_percent"]
            if value:
                history.append({"line": line, "year": str(year), "cjtPercent": float(value)})

    category_totals = defaultdict(int)
    category_months = defaultdict(set)
    for row in read_csv("data/powerbi/rpt_delay_month_line_category.csv"):
        if row["month"].startswith("2025") and row["day_type"] == "1":
            category = row["delay_category"]
            category_totals[category] += int(number(row["delay_incidents"]))
            category_months[category].add(row["month"])
    categories = [
        {"category": category, "incidents": count, "months": len(category_months[category])}
        for category, count in sorted(category_totals.items(), key=lambda item: item[1], reverse=True)
    ]

    snapshot = {
        "surface": "dashboard", "title": "MTA TransitPulse", "status": "reviewed",
        "buildStatus": "complete", "generatedAt": datetime.now(timezone.utc).isoformat(),
        "filters": [],
        "queries": {
            "annual_system": {"rows": annual, "source": source(
                "Customer journey reliability", ["data/analysis/monthly_system.csv"],
                "Passenger-weighted weekday customer journey performance; 6 a.m.–11 p.m. unlinked train trips.",
                "100 × (1 − sum(over_five_trips) / sum(passenger_trips))")},
            "monthly_system": {"rows": monthly, "source": source(
                "Monthly customer journey reliability", ["data/analysis/monthly_system.csv"],
                "Monthly passenger-weighted weekday journey performance from the validated system summary.")},
            "priority_2025": {"rows": priority, "source": source(
                "Proposed investigation priority", ["data/analysis/line_priority_2025.csv", "reports/PRIORITIZATION_METHOD.md"],
                "2025 rank among 23 comparison groups using proposed 40% reliability, 40% passenger burden, and 20% peak service weights. This is an investigation screen, not an impact estimate.")},
            "line_history": {"rows": history, "source": source(
                "Line customer journey reliability", ["data/analysis/line_priority_2025.csv"],
                "Annual customer journey performance for the 23 scorecard comparison groups; 2022 42nd Street Shuttle coverage is incomplete.")},
            "delay_categories_2025": {"rows": categories, "source": source(
                "Weekday delay-causing incidents", ["data/powerbi/rpt_delay_month_line_category.csv"],
                "2025 weekday incident counts by reporting category. Counts are diagnostic workload, not exposure-adjusted risk.")},
        },
    }

    by_year = {row["year"]: row for row in annual}
    assert abs(by_year["2022"]["cjtPercent"] - 83.882447) < 0.001
    assert abs(by_year["2025"]["cjtPercent"] - 85.402430) < 0.001
    assert abs(by_year["2025"]["netMinutes"] - 3_240_546_696) < 2
    assert [row["line"] for row in sorted(priority, key=lambda row: row["rank"])[:3]] == ["F", "B", "Q"]
    return snapshot


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    snapshot = build()
    OUTPUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if APP_DATA.exists():
        current = json.loads(APP_DATA.read_text(encoding="utf-8"))
        snapshot["id"] = current["id"]
        snapshot["exportPreferences"] = current.get("exportPreferences", {"selected": None, "destinations": []})
        APP_DATA.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = ", ".join(f"{key}: {len(value['rows'])}" for key, value in snapshot["queries"].items())
    print(f"Wrote {OUTPUT} with {counts}")
