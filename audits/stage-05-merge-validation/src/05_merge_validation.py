"""
Stage 05 — Final-master key and structural validation.

This script audits the final master workbook only. It cannot prove that a
left join preserved every row from the original base dataset, or identify
source records lost during merging, without the original source workbooks.
"""
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
STAGE_DIR = Path(__file__).resolve().parents[1]
INPUT = REPO_ROOT / "data" / "raw" / "master excel.xlsx"
REPORTS = STAGE_DIR / "reports"
SHEET = "master dataset"
KEYS = ["Country Code", "Year"]
NAME = "Country Name"


def load_master():
    """Read the master sheet without modifying the workbook."""
    return pd.read_excel(INPUT, sheet_name=SHEET)


def key_checks(df):
    """Check missing identifiers and duplicate Country Code + Year keys."""
    rows = []
    for col in [*KEYS, NAME]:
        n = int(df[col].isna().sum())
        rows.append({"check": f"missing_values:{col}",
                     "result": "PASS" if n == 0 else "REVIEW",
                     "count": n})
    duplicate_rows = int(df.duplicated(KEYS, keep=False).sum())
    rows.append({"check": "duplicate_country_code_year",
                 "result": "PASS" if duplicate_rows == 0 else "REVIEW",
                 "count": duplicate_rows})
    return pd.DataFrame(rows)


def mapping_issues(df):
    """Flag names linked to multiple codes, or codes linked to multiple names."""
    pairs = df[[NAME, "Country Code"]].dropna().drop_duplicates()
    issues = []
    for name, count in pairs.groupby(NAME)["Country Code"].nunique().items():
        if count > 1:
            issues.append({"check": "one_name_multiple_codes", "value": name,
                           "distinct_count": int(count)})
    for code, count in pairs.groupby("Country Code")[NAME].nunique().items():
        if count > 1:
            issues.append({"check": "one_code_multiple_names", "value": code,
                           "distinct_count": int(count)})
    return pd.DataFrame(issues, columns=["check", "value", "distinct_count"])


def entity_year_coverage(df):
    """Summarize each entity's year span and gaps within that span."""
    rows = []
    for (code, name), group in df.groupby(["Country Code", NAME], dropna=False):
        years = sorted(pd.to_numeric(group["Year"], errors="coerce").dropna().astype(int).unique())
        if years:
            expected = years[-1] - years[0] + 1
            gaps = expected - len(years)
            rows.append({"Country Code": code, NAME: name, "first_year": years[0],
                         "last_year": years[-1], "observed_years": len(years),
                         "expected_years_in_span": expected,
                         "missing_years_inside_span": gaps,
                         "continuous_inside_span": gaps == 0})
        else:
            rows.append({"Country Code": code, NAME: name, "first_year": None,
                         "last_year": None, "observed_years": 0,
                         "expected_years_in_span": 0,
                         "missing_years_inside_span": None,
                         "continuous_inside_span": False})
    return pd.DataFrame(rows)


def yearly_row_counts(df):
    """Count rows and entities per year; does not assume all entities should appear each year."""
    return (df.groupby("Year", dropna=False)
              .agg(row_count=("Country Code", "size"),
                   distinct_codes=("Country Code", "nunique"),
                   distinct_names=(NAME, "nunique"))
              .reset_index().sort_values("Year"))


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    df = load_master()
    checks = key_checks(df)
    issues = mapping_issues(df)
    coverage = entity_year_coverage(df)
    yearly = yearly_row_counts(df)

    checks.to_csv(REPORTS / "05_key_checks.csv", index=False)
    issues.to_csv(REPORTS / "05_country_code_name_issues.csv", index=False)
    coverage.to_csv(REPORTS / "05_entity_year_coverage.csv", index=False)
    yearly.to_csv(REPORTS / "05_yearly_row_counts.csv", index=False)

    missing_keys = int(df[KEYS].isna().any(axis=1).sum())
    duplicate_rows = int(df.duplicated(KEYS, keep=False).sum())
    entities_with_gaps = int((coverage["missing_years_inside_span"].fillna(0) > 0).sum())
    summary = f"""STAGE 05 — FINAL MASTER KEY AND STRUCTURAL VALIDATION
====================================================
Input: {INPUT.name} | sheet: {SHEET}
Rows: {len(df):,}
Columns: {len(df.columns):,}
Distinct country codes/entities: {df['Country Code'].nunique(dropna=True):,}
Year range: {int(pd.to_numeric(df['Year'], errors='coerce').min())}–{int(pd.to_numeric(df['Year'], errors='coerce').max())}

RESULTS
-------
Rows with missing Country Code or Year: {missing_keys:,}
Rows involved in duplicate Country Code + Year keys: {duplicate_rows:,}
Country-code/name mapping issues flagged: {len(issues):,}
Entities with a gap inside their first-to-last year span: {entities_with_gaps:,}

INTERPRETATION
--------------
These checks test internal consistency of the final master dataset.
A continuous year span does not mean every variable is available.
A country-year gap is not automatically an error; an entity may begin reporting
later or stop earlier.

CRITICAL LIMITATION
-------------------
This workbook alone cannot establish which join type was used or prove that
all base-table rows were preserved. To validate an actual left join, we need
the original base workbook and source files (or saved intermediate merges),
then compare keys before and after each merge.

No source data was changed. This script only writes audit reports.
"""
    (REPORTS / "05_merge_validation_summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
