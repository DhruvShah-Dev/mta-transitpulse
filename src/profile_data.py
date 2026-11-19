"""Write a compact raw-source profile. Run: python src/profile_data.py"""

import json
from pathlib import Path
import pandas as pd

from clean_data import FILES, KEYS, RAW, ROOT, SCHEMAS


def main():
    profile = {}
    for source, filename in FILES.items():
        frame = pd.read_csv(RAW / filename, keep_default_na=False, dtype=str)
        profile[source] = {
            "file": str((RAW / filename).relative_to(ROOT)),
            "rows": len(frame),
            "columns": list(frame.columns),
            "schema_matches_expected": list(frame.columns) == SCHEMAS[source],
            "first_month": frame.month.min()[:10],
            "last_month": frame.month.max()[:10],
            "distinct_months": int(frame.month.nunique()),
            "duplicate_grain_rows": int(frame.duplicated(KEYS[source]).sum()),
            "blank_by_column": {col: int(frame[col].eq("").sum()) for col in frame},
            "lines": sorted(frame.line.unique().tolist()),
        }
    out = ROOT / "data" / "validation" / "raw_profile.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
