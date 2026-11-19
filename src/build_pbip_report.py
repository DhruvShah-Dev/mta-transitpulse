"""Author four TransitPulse PBIR pages in the existing user-created project."""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "dashboards" / "TransitPulse.Report" / "definition"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
METRICS = "rpt_customer_month_line_period"

def ident(seed):
    return uuid.uuid5(uuid.NAMESPACE_URL, "transitpulse:" + seed).hex[:20]

def lit(value):
    if isinstance(value, bool):
        value = "true" if value else "false"
    elif isinstance(value, (float, int)):
        value = f"{value}D"
    else:
        value = "'" + value.replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": value}}}

def field(table, name, kind="Column"):
    return {"field": {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}},
            "queryRef": f"{table}.{name}", "nativeQueryRef": name}

def item(seed, visual_type, x, y, w, h, roles=None, title=None, objects=None, sort=None):
    number = int(seed.rsplit("-", 1)[1])
    visual = {"visualType": visual_type}
    if roles:
        visual["query"] = {"queryState": {role: {"projections": values} for role, values in roles.items()}}
    if sort:
        table, name, kind, direction = sort
        visual["query"]["sortDefinition"] = {
            "sort": [{"field": field(table, name, kind)["field"], "direction": direction}],
            "isDefaultSort": False}
    if objects:
        visual["objects"] = objects
    if title:
        visual["visualContainerObjects"] = {"title": [{"properties": {
            "show": lit(True), "text": lit(title), "fontSize": lit(13)}}]}
    return {"$schema": SCHEMA, "name": ident(seed),
            "position": {"x": x, "y": y, "z": number * 1000, "height": h, "width": w, "tabOrder": number},
            "visual": visual}

def text(seed, content, x, y, w, h, size=18, color="#17324D", bold=False):
    if size >= 36:
        h = max(h, 80)
    if size == 17 and y in (102, 105):
        y, h = 112, max(h, 48)
    style = {"fontFamily": "Segoe UI Semibold" if bold else "Segoe UI",
             "fontSize": f"{size}px", "color": color}
    return item(seed, "textbox", x, y, w, h, objects={"general": [{"properties": {
        "paragraphs": [{"textRuns": [{"value": content, "textStyle": style}],
                        "horizontalTextAlignment": "left"}]}}]})

def card(seed, measure, x, y, w=440):
    return item(seed, "cardVisual", x, y, w, 160, {"Data": [field(METRICS, measure, "Measure")]},
                objects={"value": [{"properties": {"fontSize": lit(38)}, "selector": {"id": "default"}}],
                         "label": [{"properties": {"fontSize": lit(15)}, "selector": {"id": "default"}}]})

def slicer(seed, table, column, label, x, y, w=220):
    return item(seed, "slicer", x, y, w, 84, {"Values": [field(table, column)]},
                objects={"data": [{"properties": {"mode": lit("Dropdown")}}],
                         "header": [{"properties": {"show": lit(True), "text": lit(label)}}]})

def chart(seed, visual_type, title, x, y, w, h, category, measures, sort=None):
    return item(seed, visual_type, x, y, w, h, {
        "Category": [field(*category)],
        "Y": [field(METRICS, name, "Measure") for name in measures]}, title, sort=sort)

def table(seed, title, x, y, w, h, columns, sort=None, show_total=True):
    objects = {"columnHeaders": [{"properties": {"autoSizeColumnWidth": lit(True),
                                               "columnAdjustment": lit("growToFit")}}]}
    if not show_total:
        objects["total"] = [{"properties": {"totals": lit(False)}}]
    return item(seed, "tableEx", x, y, w, h,
                {"Values": [field(*column) for column in columns]}, title, objects, sort=sort)

def scatter(seed, title, x, y, w, h, group, xname, yname, size=None, series=None):
    roles = {"Category": [field(*group)],
             "X": [field(METRICS, xname, "Measure")],
             "Y": [field(METRICS, yname, "Measure")]}
    if size:
        roles["Size"] = [field(METRICS, size, "Measure")]
    if series:
        roles["Series"] = [field(*series)]
    return item(seed, "scatterChart", x, y, w, h, roles, title)

def pages():
    month = ("rpt_dim_month", "month")
    line = ("rpt_dim_line", "line_id")
    out = []
    overview = [
        text("overview-1", "MTA TransitPulse", 50, 30, 900, 66, 38, bold=True),
        text("overview-2", "SUBWAY RELIABILITY & PASSENGER IMPACT  |  2022–2025", 52, 102, 1120, 36, 17, "#507188"),
        slicer("overview-3", *line, "Line group", 1610, 50, 250),
        card("overview-4", "2025 CJTP %", 50, 170, 520),
        card("overview-5", "2025 Net Minutes (billions)", 590, 170, 600),
        text("overview-6", "2025 FIRST INVESTIGATION: F · B · Q", 1230, 195, 620, 90, 25, "#B8402F", True),
        chart("overview-7", "lineChart", "Passenger-weighted CJTP by month", 50, 365, 880, 430, month, ["CJTP %"]),
        chart("overview-8", "lineChart", "Net additional passenger minutes by month", 960, 365, 880, 430, month, ["Net Additional Passenger Minutes"]),
        text("overview-9", "D  |  Targeted reliability review: second-lowest 2025 CJTP", 50, 840, 1400, 60, 21, "#A45B12", True),
        text("overview-10", "2025 cards are fixed annual baselines; line selection applies. Net minutes are signed estimates. Source: MTA open data.", 50, 990, 1820, 48, 16, "#5D7182"),
    ]
    out.append(("Executive Overview", "overview", overview))
    performance = [
        text("performance-1", "Subway Line Performance", 50, 30, 1100, 66, 36, bold=True),
        text("performance-2", "Compare customer reliability, time burden, and their components", 52, 105, 1050, 36, 17, "#507188"),
        slicer("performance-12", "rpt_dim_month", "month", "Month", 1140, 50, 230),
        slicer("performance-3", "rpt_dim_month", "year", "Year", 1390, 50, 210),
        slicer("performance-4", *line, "Line group", 1620, 50, 240),
        card("performance-5", "CJTP %", 50, 165),
        card("performance-6", "AJT Minutes Per Trip", 510, 165),
        card("performance-7", "CJTP YoY Change pp", 970, 165),
        chart("performance-8", "lineChart", "Monthly CJTP", 50, 345, 870, 360, month, ["CJTP %"]),
        chart("performance-9", "clusteredBarChart", "CJTP by line group", 950, 345, 910, 360, line, ["CJTP %"],
              sort=(METRICS, "CJTP %", "Measure", "Ascending")),
        table("performance-10", "Journey outcomes by line", 50, 735, 1810, 260,
              [("rpt_dim_line", "line_id")] + [(METRICS, name, "Measure") for name in
              ["CJTP %", "AJT Minutes Per Trip", "APT Minutes Per Trip",
               "ATT Minutes Per Trip", "Net Additional Passenger Minutes (M)"]]),
        text("performance-11", "Percentages and per-trip values use summed numerators and trips. Negative train time remains signed; NW combines N/W.", 50, 1015, 1810, 42, 15, "#5D7182"),
    ]
    out.append(("Subway Line Performance", "performance", performance))
    diagnostics = [
        text("diagnostics-1", "Operational Diagnostics", 50, 30, 1000, 66, 36, bold=True),
        text("diagnostics-2", "Incident patterns and service delivery are diagnostic evidence", 52, 105, 1220, 36, 17, "#507188"),
        slicer("diagnostics-3", "rpt_dim_month", "year", "Year", 1175, 50, 190),
        slicer("diagnostics-4", *line, "Line group", 1385, 50, 220),
        slicer("diagnostics-5", "rpt_dim_delay_category", "delay_category", "Delay category", 1625, 50, 235),
        card("diagnostics-6", "Weekday Delay Incidents", 50, 170, 420),
        card("diagnostics-7", "Weekday Peak Service Delivered %", 490, 170, 500),
        card("diagnostics-8", "Weekday Major Incidents", 1010, 170, 420),
        chart("diagnostics-9", "clusteredBarChart", "Weekday delay incidents by category", 50, 350, 870, 350,
              ("rpt_dim_delay_category", "delay_category"), ["Weekday Delay Incidents"]),
        chart("diagnostics-10", "lineChart", "Weekday peak Service Delivered by month", 950, 350, 910, 350, month, ["Weekday Peak Service Delivered %"]),
        scatter("diagnostics-11", "Incident count and CJTP by line — association only", 50, 725, 870, 270, line, "Weekday Delay Incidents", "CJTP %"),
        chart("diagnostics-12", "lineChart", "Weekday delay incidents by month", 950, 725, 910, 270, month, ["Weekday Delay Incidents"]),
        text("diagnostics-13", "Incidents cover all weekday hours; service covers selected peaks. Major incidents are separate. Missing is not zero. Service may exceed 100%.", 50, 1010, 1810, 48, 15, "#5D7182"),
    ]
    out.append(("Operational Diagnostics", "diagnostics", diagnostics))
    priorities = [
        text("priorities-1", "Operational Priorities", 50, 30, 1100, 66, 36, bold=True),
        text("priorities-2", "FIXED 2025 SCORECARD  |  Proposed weights: reliability 40% · burden 40% · service 20%", 52, 105, 1450, 36, 17, "#507188"),
        slicer("priorities-3", *line, "Line group", 1620, 50, 240),
        scatter("priorities-4", "Customer reliability vs passenger-time burden", 50, 175, 880, 550, line,
                "2025 Priority CJTP %", "2025 Priority Net Minutes (M)", "2025 Priority Passenger Trips",
                series=("rpt_priority_2025", "priority_quadrant")),
        table("priorities-5", "2025 line priority scorecard", 960, 175, 900, 550,
              [("rpt_priority_2025", name) for name in
               ["line_id", "rank_baseline", "review_status", "cjt_percent"]] +
              [(METRICS, "2025 Priority Net Minutes (M)", "Measure"),
               ("rpt_priority_2025", "score_baseline")],
              sort=("rpt_priority_2025", "rank_baseline", "Column", "Ascending"), show_total=False),
        table("priorities-6", "Rank sensitivity across proposed weights", 50, 750, 1810, 230,
              [("rpt_priority_2025", name) for name in
               ["line_id", "rank_baseline", "rank_equal", "rank_reliability_focused",
                "rank_burden_focused", "rank_service_focused"]],
              sort=("rpt_priority_2025", "rank_baseline", "Column", "Ascending")),
        text("priorities-7", "F, B, Q lead first review; D needs targeted reliability review. Quadrant medians: 84.95% CJTP / 161.36M net minutes. Proposed ranks are not MTA weights.", 50, 1000, 1810, 50, 15, "#5D7182"),
    ]
    out.append(("Operational Priorities", "priorities", priorities))
    return out

def main():
    all_pages = pages()
    names = []
    for display, slug, visuals in all_pages:
        name = ident("page-" + slug)
        names.append(name)
        folder = DEST / "pages" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "page.json").write_text(json.dumps({
            "$schema": PAGE_SCHEMA, "name": name, "displayName": display,
            "displayOption": "FitToPage", "height": 1080, "width": 1920}, indent=2), encoding="utf-8")
        for v in visuals:
            target = folder / "visuals" / v["name"]
            target.mkdir(parents=True, exist_ok=True)
            (target / "visual.json").write_text(json.dumps(v, indent=2), encoding="utf-8")
    (DEST / "pages" / "pages.json").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": names, "activePageName": names[0]}, indent=2), encoding="utf-8")
    print(", ".join(f"{name}: {len(visuals)} visuals" for name, _, visuals in all_pages))

if __name__ == "__main__":
    main()
