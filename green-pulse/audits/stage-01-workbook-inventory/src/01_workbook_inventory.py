"""Stage 01: inspect workbook structure without changing the source data.

Run from the project folder:
    python audits/stage-01-workbook-inventory/src/01_workbook_inventory.py

Outputs a text report under reports/. This script does not clean or overwrite data.
"""
from pathlib import Path
from datetime import datetime
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
STAGE_DIR = Path(__file__).resolve().parents[1]
# Keep the original workbook in data/raw/; never edit it in place.
INPUT_FILE = REPO_ROOT / "data" / "raw" / "master excel.xlsx"
REPORT_DIR = STAGE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Workbook not found: {INPUT_FILE}\n"
            "Copy your original Excel workbook into data/raw/ without changing its name."
        )

    lines = []
    lines.append("STAGE 01 — WORKBOOK INVENTORY")
    lines.append(f"Run time: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Input file: {INPUT_FILE.name}")

    excel = pd.ExcelFile(INPUT_FILE)
    lines.append(f"Sheets: {excel.sheet_names}")

    for sheet_name in excel.sheet_names:
        df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name)
        lines.append("\n" + "=" * 72)
        lines.append(f"SHEET: {sheet_name}")
        lines.append(f"Rows: {len(df):,}")
        lines.append(f"Columns: {len(df.columns):,}")
        lines.append("\nCOLUMN NAMES AND DATA TYPES")
        for col in df.columns:
            lines.append(f"- {col!r}: {df[col].dtype}")

        lines.append("\nMISSING VALUES BY COLUMN")
        missing = df.isna().sum().sort_values(ascending=False)
        for col, count in missing.items():
            pct = count / len(df) * 100 if len(df) else 0
            lines.append(f"- {col}: {count:,} ({pct:.2f}%)")

        lines.append("\nDUPLICATE CHECKS")
        lines.append(f"- Completely duplicated rows: {df.duplicated().sum():,}")
        key_cols = [c for c in ["Country Name", "Country Code", "Year"] if c in df.columns]
        if len(key_cols) == 3:
            lines.append(f"- Duplicate Country Name + Country Code + Year keys: {df.duplicated(key_cols).sum():,}")
        if all(c in df.columns for c in ["Country Code", "Year"]):
            lines.append(f"- Duplicate Country Code + Year keys: {df.duplicated(['Country Code', 'Year']).sum():,}")

        lines.append("\nSAMPLE ROWS (first 5; display only)")
        lines.append(df.head(5).to_string(index=False))

    output = REPORT_DIR / "01_workbook_inventory.txt"
    output.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nSaved report to: {output}")


if __name__ == "__main__":
    main()
