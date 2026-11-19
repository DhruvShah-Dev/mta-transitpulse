"""Populate the TransitPulse PBIP with portable snapshots of validated CSVs.

The Import model embeds compressed reporting snapshots so the portfolio PBIP
opens and refreshes after a clone. Regenerate it after build_powerbi_reporting.py.
"""

import base64
import gzip
import re
import uuid
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFINITION = ROOT / "dashboards" / "TransitPulse.SemanticModel" / "definition"
DATA = ROOT / "data" / "powerbi"
MEASURE_FILE = ROOT / "dashboards" / "TransitPulseModel" / "MEASURES.dax"


def dtype_for(series: pd.Series, name: str) -> tuple[str, str]:
    if name == "month":
        return "dateTime", "type date"
    kind = series.dtype.kind
    if kind == "b":
        return "boolean", "type logical"
    if kind in "iu":
        return "int64", "Int64.Type"
    if kind == "f":
        return "double", "type number"
    return "string", "type text"


def parse_measures() -> list[tuple[str, str]]:
    text = MEASURE_FILE.read_text(encoding="utf-8")
    sections = re.split(r"(?m)^([A-Za-z0-9][A-Za-z0-9 %()]*) =\s*\n", text)
    measures = []
    for i in range(1, len(sections), 2):
        name = sections[i].strip()
        expression = "\n".join(
            line for line in sections[i + 1].splitlines() if not line.lstrip().startswith("//")
        ).strip()
        if expression:
            measures.append((name, expression))
    return measures


def tmdl_table(path: Path, measures: list[tuple[str, str]]) -> str:
    name = path.stem
    data = pd.read_csv(path)
    lines = [f"table {name}", ""]
    for column in data.columns:
        datatype, _ = dtype_for(data[column], column)
        lines.extend([f"\tcolumn {column}", f"\t\tdataType: {datatype}",
                      f"\t\tsourceColumn: {column}", "\t\tsummarizeBy: none"])
        if column in {"month", "line_id"} and name.startswith("rpt_dim_"):
            lines.append("\t\tisKey")
        if column == "month_label":
            lines.append("\t\tsortByColumn: month")
        if name.startswith("rpt_") and not name.startswith("rpt_dim_") and column in {
            "passenger_trips", "over_five_trips", "platform_minutes", "train_minutes",
            "net_additional_passenger_minutes", "delay_incidents", "major_incidents",
            "scheduled_peak_trains", "actual_peak_trains",
        }:
            lines.append("\t\tisHidden")
        lines.append("")
    if name == "rpt_customer_month_line_period":
        for measure_name, expression in measures:
            if "\n" in expression:
                lines.append(f"\tmeasure '{measure_name}' =")
                lines.extend(f"\t\t\t{line}" for line in expression.splitlines())
            else:
                lines.append(f"\tmeasure '{measure_name}' = {expression}")
            if measure_name in {"CJTP %", "Previous Year CJTP %", "2025 CJTP %", "Weekday Peak Service Delivered %"}:
                lines.append("\t\tformatString: 0.00%")
            elif measure_name == "2025 Priority CJTP %":
                lines.append("\t\tformatString: 0.00")
            elif measure_name == "2025 Net Minutes (billions)":
                lines.append("\t\tformatString: 0.00\"B\"")
            elif measure_name.endswith("(M)"):
                lines.append("\t\tformatString: 0.0")
            elif measure_name.endswith("pp"):
                lines.append("\t\tformatString: +0.00;-0.00;0.00")
            elif "Per Trip" in measure_name:
                lines.append("\t\tformatString: 0.00")
            elif "Score" in measure_name:
                lines.append("\t\tformatString: 0.0")
            else:
                lines.append("\t\tformatString: #,0")
            lines.append("")
    # Embed compressed, validated CSV snapshots to keep the PBIP portable.
    # Refresh the snapshots by regenerating the model after the reporting layer.
    column_types = ", ".join(
        '{{"{}", {}}}'.format(column, dtype_for(data[column], column)[1])
        for column in data.columns
    )
    encoded = base64.b64encode(gzip.compress(path.read_bytes(), mtime=0)).decode("ascii")
    chunks = [encoded[i:i + 1000] for i in range(0, len(encoded), 1000)]
    lines.extend([f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =",
                  "\t\t\tlet",
                  "\t\t\t    Encoded = Text.Combine({"])
    lines.extend(f'\t\t\t        "{chunk}"{"," if index < len(chunks) - 1 else ""}'
                 for index, chunk in enumerate(chunks))
    lines.extend(["\t\t\t    }, \"\"),",
                  '\t\t\t    Source = Csv.Document(Binary.Decompress(Binary.FromText(Encoded, BinaryEncoding.Base64), Compression.GZip), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
                  "\t\t\t    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                  f'\t\t\t    Typed = Table.TransformColumnTypes(Headers, {{{column_types}}}, "en-US")',
                  "\t\t\tin", "\t\t\t    Typed", ""])
    return "\n".join(lines)


def main() -> None:
    if not (ROOT / "dashboards" / "TransitPulse.pbip").exists():
        raise RuntimeError("Expected the user-created dashboards/TransitPulse.pbip")
    paths = sorted(DATA.glob("rpt_*.csv"))
    if len(paths) != 9:
        raise RuntimeError("Build the nine Power BI reporting exports first")
    measures = parse_measures()
    if len(measures) < 15:
        raise RuntimeError("DAX measure draft parsing failed")
    tables_dir = DEFINITION / "tables"
    tables_dir.mkdir(exist_ok=True)
    for path in paths:
        (tables_dir / f"{path.stem}.tmdl").write_text(tmdl_table(path, measures), encoding="utf-8")
    model_path = DEFINITION / "model.tmdl"
    model = model_path.read_text(encoding="utf-8-sig")
    model = re.sub(r"(?m)^ref table rpt_.*\n", "", model)
    refs = "".join(f"ref table {path.stem}\n" for path in paths)
    if "ref culture" in model:
        model = model.replace("ref culture", refs + "\nref culture", 1)
    else:
        model += "\n" + refs
    model_path.write_text(model, encoding="utf-8")
    facts = ["rpt_customer_month_line_period", "rpt_delay_month_line_category",
             "rpt_major_month_line_category", "rpt_service_month_line_daytype"]
    pairs = [(fact, "month", "rpt_dim_month", "month") for fact in facts]
    pairs += [(fact, "line_id", "rpt_dim_line", "line_id") for fact in facts + ["rpt_priority_2025"]]
    pairs += [("rpt_delay_month_line_category", "delay_category", "rpt_dim_delay_category", "delay_category"),
              ("rpt_major_month_line_category", "major_category", "rpt_dim_major_category", "major_category")]
    relationship_lines = []
    for fact, fact_key, dim, dim_key in pairs:
        relationship_lines.extend([
            f"relationship {uuid.uuid5(uuid.NAMESPACE_URL, f'mta:{fact}:{fact_key}:{dim}')}" ,
            f"\tfromColumn: {fact}.{fact_key}", f"\ttoColumn: {dim}.{dim_key}",
            "\tfromCardinality: many", "\ttoCardinality: one",
            "\tcrossFilteringBehavior: oneDirection", "",
        ])
    (DEFINITION / "relationships.tmdl").write_text("\n".join(relationship_lines), encoding="utf-8")
    print(f"Wrote {len(paths)} TMDL tables, {len(measures)} measures, and {len(pairs)} relationships")


if __name__ == "__main__":
    main()
