"""Download the MTA TransitPulse baseline from New York State Open Data.

Run from this folder with: python download_data.py
The script uses only the Python standard library.
"""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
DOCS = ROOT / "data" / "documentation"
META = ROOT / "data" / "metadata"
START = "2022-01-01T00:00:00"
END_EXCLUSIVE = "2026-01-01T00:00:00"
DATASETS = {
    "r7qk-6tcy": "subway_customer_journey.csv",
    "g937-7k7c": "subway_delay_incidents.csv",
    "ereg-mcvp": "subway_major_incidents.csv",
    "32ch-sei3": "subway_service_delivered.csv",
}


def download(url, destination):
    temporary = destination.with_name(destination.name + ".part")
    with urlopen(url, timeout=120) as response, temporary.open("wb") as target:
        while chunk := response.read(1024 * 1024):
            target.write(chunk)
    temporary.replace(destination)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    for directory in (RAW, DOCS, META):
        directory.mkdir(parents=True, exist_ok=True)
    manifest = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "period_start": START[:10],
        "period_end_inclusive": "2025-12-31",
        "datasets": [],
    }
    where = f"month >= '{START}' AND month < '{END_EXCLUSIVE}'"
    for dataset_id, filename in DATASETS.items():
        metadata_url = f"https://data.ny.gov/api/views/{dataset_id}.json"
        with urlopen(metadata_url, timeout=60) as response:
            metadata = json.load(response)
        metadata_path = META / f"{dataset_id}.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        query = urlencode({"$where": where, "$limit": 1000000, "$order": "month,line"})
        csv_url = f"https://data.ny.gov/resource/{dataset_id}.csv?{query}"
        csv_path = RAW / filename
        download(csv_url, csv_path)
        with csv_path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            columns = reader.fieldnames
            row_count = sum(1 for _ in reader)
        if not columns or row_count == 0:
            raise RuntimeError(f"Empty CSV: {csv_path}")
        count_query = urlencode({"$select": "count(*) as n", "$where": where})
        count_url = f"https://data.ny.gov/resource/{dataset_id}.json?{count_query}"
        with urlopen(count_url, timeout=60) as response:
            expected_rows = int(json.load(response)[0]["n"])
        if row_count != expected_rows:
            raise RuntimeError(
                f"Incomplete CSV for {dataset_id}: downloaded {row_count} of {expected_rows} rows"
            )

        attachments = []
        for attachment in metadata.get("metadata", {}).get("attachments", []):
            asset_id = attachment.get("assetId")
            name = attachment.get("filename") or attachment.get("name")
            if not asset_id or not name or not name.lower().endswith(".pdf"):
                continue
            attachment_url = f"https://data.ny.gov/api/views/{dataset_id}/files/{asset_id}?download=true"
            attachment_path = DOCS / name
            download(attachment_url, attachment_path)
            attachments.append({
                "file": str(attachment_path.relative_to(ROOT)),
                "url": attachment_url,
                "bytes": attachment_path.stat().st_size,
                "sha256": sha256(attachment_path),
            })

        manifest["datasets"].append({
            "id": dataset_id,
            "title": metadata.get("name"),
            "page": f"https://data.ny.gov/d/{dataset_id}",
            "api_url": csv_url,
            "metadata_url": metadata_url,
            "csv_file": str(csv_path.relative_to(ROOT)),
            "metadata_file": str(metadata_path.relative_to(ROOT)),
            "rows": row_count,
            "api_count": expected_rows,
            "columns": columns,
            "bytes": csv_path.stat().st_size,
            "sha256": sha256(csv_path),
            "attachments": attachments,
        })
        print(f"{dataset_id}: {row_count:,} rows, {len(attachments)} PDFs")
    (ROOT / "data" / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
