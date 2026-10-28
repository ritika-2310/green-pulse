"""Stage 02: profile columns and create a provisional data dictionary.

This is a read-only audit. It does not alter the source workbook.
Run from the project root: python src/02_column_semantics.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "raw" / "master excel.xlsx"
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
SHEET_NAME = "master dataset"

# Descriptions are provisional, based on column names and observed values.
# Confirm exact definitions, units and source against the original source files/metadata.
DICTIONARY = {
    "Country Name": ("Name of the country or entity represented by the row.", "Text", "Identifier", "Includes aggregate entities as well as countries; distinguish these in analysis."),
    "Country Code": ("Code identifying the country or entity.", "Text/code", "Identifier", "Confirm code standard and aggregate codes against source metadata."),
    "Year": ("Year associated with the observation.", "Calendar year (assumed)", "Time index", "Integer year; each row is intended to represent an entity-year."),
    "GDP": ("Gross domestic product, an indicator of economic output.", "Unknown from workbook alone", "Economic measure", "Must verify currency, price basis, scale and source before interpreting growth."),
    "Inflation": ("Inflation rate or price-level change indicator.", "Likely percent; verify", "Economic measure", "Confirm exact definition and whether annual percentage change."),
    "Trade": ("Trade-related indicator.", "Likely percent of GDP; verify", "Economic measure", "Could represent trade as a share of GDP; verify source definition."),
    "Region": ("Geographic region classification.", "Category", "Grouping variable", "Missing for some aggregate entities may be expected."),
    "IncomeGroup": ("Income-group classification.", "Category", "Grouping variable", "Confirm classification scheme and year; missing for aggregates may be expected."),
    "population": ("Population associated with the entity and year.", "People; verify source", "Demographic measure", "Check whether source uses persons, thousands, or another scale."),
    "carbon_intensity_elec": ("Carbon intensity of electricity generation/use.", "Unknown; likely emissions per unit electricity", "Energy/environment measure", "Confirm unit and whether generation- or consumption-based."),
    "electricity_demand": ("Electricity demand or consumption measure.", "Unknown", "Energy measure", "Verify unit and exact concept; do not assume it equals generation."),
    "electricity_generation": ("Electricity generated.", "Unknown", "Energy measure", "Verify unit and whether values are total generation or another measure."),
    "energy_per_capita": ("Energy use per person.", "Unknown", "Energy measure", "Verify energy unit and population basis."),
    "energy_per_gdp": ("Energy use relative to economic output.", "Unknown", "Energy/economic intensity", "Verify numerator, GDP basis, units and direction of indicator."),
    "fossil_share_elec": ("Share of electricity associated with fossil fuels.", "Likely percent; verify", "Energy mix measure", "Check expected range and source definition."),
    "fossil_share_energy": ("Share of energy associated with fossil fuels.", "Likely percent; verify", "Energy mix measure", "Check expected range and source definition."),
    "greenhouse_gas_emissions": ("Greenhouse-gas emissions measure.", "Unknown", "Emissions measure", "Verify gases included, units, scale and whether per capita/intensity/total."),
    "low_carbon_share_elec": ("Share of electricity from low-carbon sources.", "Likely percent; verify", "Energy mix measure", "Confirm low-carbon definition and source."),
    "low_carbon_share_energy": ("Share of energy from low-carbon sources.", "Likely percent; verify", "Energy mix measure", "Confirm low-carbon definition and source."),
    "Annual CO2 emissions": ("Annual carbon-dioxide emissions.", "Unknown; possibly tonnes", "Emissions measure", "Verify unit, gases, territorial/accounting basis and source."),
    "CO2 emissions per capita": ("CO2 emissions divided by population.", "Unknown; possibly tonnes/person", "Emissions intensity measure", "Verify units and whether values were computed or sourced."),
    "Share of global annual CO₂ emissions": ("Entity's share of global annual CO2 emissions.", "Fraction or percent; verify", "Emissions share measure", "Observed values look fractional in sample; verify whether 0.01 means 1%."),
    "GDP Growth (%)": ("Percentage change in GDP between periods, or a sourced growth indicator.", "Percent", "Derived or sourced indicator", "Formula/source not yet confirmed; validate first-year and gap handling in Stage 06."),
    "CO2 Growth (%)": ("Percentage change in CO2 emissions between periods, or a sourced growth indicator.", "Percent", "Derived or sourced indicator", "Formula/source not yet confirmed; validate year gaps, zeros and first-year values in Stage 06."),
    "Decoupling Status": ("Category describing the relationship between economic growth and emissions change.", "Category", "Derived indicator", "Exact decision rules are unknown; document and independently validate before use."),
    "Transition Risk Score": ("A score intended to represent transition-related risk.", "Unknown scale", "Derived indicator", "Definition, inputs, weighting and interpretation are unknown; do not treat as validated yet."),
}


def fmt_examples(series: pd.Series, n: int = 5) -> str:
    vals = series.dropna().head(n).tolist()
    return " | ".join(str(v) for v in vals)


def main() -> None:
    if not INPUT.exists():
        raise FileNotFoundError(f"Input workbook not found: {INPUT}")
    xls = pd.ExcelFile(INPUT)
    if SHEET_NAME not in xls.sheet_names:
        raise ValueError(f"Expected sheet {SHEET_NAME!r}; found {xls.sheet_names}")
    df = pd.read_excel(INPUT, sheet_name=SHEET_NAME)

    profiles = []
    for col in df.columns:
        s = df[col]
        non_null = s.dropna()
        row = {
            "column": col,
            "pandas_dtype": str(s.dtype),
            "rows_total": len(s),
            "non_null_count": int(s.notna().sum()),
            "missing_count": int(s.isna().sum()),
            "missing_percent": round(float(s.isna().mean() * 100), 2),
            "unique_non_null": int(non_null.nunique()),
            "example_values": fmt_examples(s),
            "min_if_numeric": None,
            "median_if_numeric": None,
            "max_if_numeric": None,
            "provisional_meaning": DICTIONARY.get(col, ("Definition not documented", "Unknown", "Unclassified", "Needs review"))[0],
            "unit_to_verify": DICTIONARY.get(col, ("", "Unknown", "", ""))[1],
            "provisional_role": DICTIONARY.get(col, ("", "", "Unclassified", ""))[2],
            "audit_notes": DICTIONARY.get(col, ("", "", "", "Definition/source needs confirmation"))[3],
        }
        if pd.api.types.is_numeric_dtype(s) and len(non_null):
            row["min_if_numeric"] = float(non_null.min())
            row["median_if_numeric"] = float(non_null.median())
            row["max_if_numeric"] = float(non_null.max())
        profiles.append(row)

    profile_df = pd.DataFrame(profiles)
    profile_csv = REPORT_DIR / "02_column_profile.csv"
    dictionary_csv = REPORT_DIR / "02_column_dictionary.csv"
    profile_df.to_csv(profile_csv, index=False)
    profile_df[["column", "provisional_meaning", "unit_to_verify", "pandas_dtype", "provisional_role", "audit_notes"]].to_csv(dictionary_csv, index=False)

    lines = [
        "STAGE 02 — COLUMN SEMANTICS AND PROFILE",
        "=" * 48,
        f"Input: {INPUT.name}",
        f"Sheet: {SHEET_NAME}",
        f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns",
        "",
        "IMPORTANT: meanings and units below are provisional, inferred from names and observed values.",
        "Confirm them using source documentation before drawing substantive conclusions.",
        "",
    ]
    for _, r in profile_df.iterrows():
        lines += [
            f"COLUMN: {r['column']}",
            f"  Detected type: {r['pandas_dtype']} | Unique non-null: {r['unique_non_null']:,}",
            f"  Missing: {r['missing_count']:,}/{r['rows_total']:,} ({r['missing_percent']}%)",
            f"  Provisional meaning: {r['provisional_meaning']}",
            f"  Unit to verify: {r['unit_to_verify']}",
            f"  Role: {r['provisional_role']}",
            f"  Examples: {r['example_values']}",
            f"  Audit note: {r['audit_notes']}",
        ]
        if pd.api.types.is_numeric_dtype(df[r['column']]):
            lines.append(f"  Numeric min / median / max: {r['min_if_numeric']} / {r['median_if_numeric']} / {r['max_if_numeric']}")
        lines.append("")
    lines += [
        "NEXT QUESTIONS TO RESOLVE",
        "1. What are the exact source and units for GDP, population, electricity and emissions columns?",
        "2. Are GDP Growth (%) and CO2 Growth (%) calculated columns or source-provided values?",
        "3. What formula and thresholds define Decoupling Status and Transition Risk Score?",
        "4. Are aggregate entities (World, regions, income groups) mixed with country-level records?",
        "",
        "Files written:",
        f"- {profile_csv.relative_to(ROOT)}",
        f"- {dictionary_csv.relative_to(ROOT)}",
    ]
    report_path = REPORT_DIR / "02_column_semantics.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {report_path}")
    print(f"Wrote {profile_csv}")
    print(f"Wrote {dictionary_csv}")


if __name__ == "__main__":
    main()
