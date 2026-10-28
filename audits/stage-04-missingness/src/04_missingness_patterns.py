"""Stage 04: Missingness pattern audit. Read-only with respect to source workbook."""
from pathlib import Path
from itertools import combinations
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
STAGE_DIR = Path(__file__).resolve().parents[1]
INPUT = REPO_ROOT / "data" / "raw" / "master excel.xlsx"
OUT = STAGE_DIR / "reports"
OUT.mkdir(parents=True, exist_ok=True)
SHEET = "master dataset"
ENTITY = "Country Name"
YEAR = "Year"

# Pairs reflect plausible research relationships, not conclusions or causal claims.
RESEARCH_PAIRS = [
    ("GDP", "Annual CO2 emissions", "GDP and total CO2 emissions"),
    ("GDP", "CO2 emissions per capita", "GDP and CO2 emissions per capita"),
    ("GDP", "GDP Growth (%)", "GDP level and GDP growth"),
    ("Annual CO2 emissions", "CO2 Growth (%)", "CO2 level and CO2 growth"),
    ("electricity_generation", "low_carbon_share_elec", "Electricity generation and low-carbon electricity share"),
    ("fossil_share_energy", "low_carbon_share_energy", "Fossil and low-carbon share of energy"),
    ("energy_per_capita", "Annual CO2 emissions", "Energy per capita and total CO2 emissions"),
    ("energy_per_gdp", "Annual CO2 emissions", "Energy per GDP and total CO2 emissions"),
    ("greenhouse_gas_emissions", "GDP", "GDP and greenhouse-gas emissions"),
    ("carbon_intensity_elec", "low_carbon_share_elec", "Electricity carbon intensity and low-carbon share"),
]

def load_data():
    if not INPUT.exists():
        raise FileNotFoundError(f"Expected workbook at {INPUT}. Put the original workbook in data/raw/.")
    df = pd.read_excel(INPUT, sheet_name=SHEET)
    if ENTITY not in df or YEAR not in df:
        raise ValueError(f"Required columns {ENTITY!r} and {YEAR!r} not found.")
    return df

def build_missingness_tables(df):
    cols = list(df.columns)
    total = len(df)
    overall = pd.DataFrame({
        "column": cols,
        "dtype": [str(df[c].dtype) for c in cols],
        "total_rows": total,
        "missing_count": [int(df[c].isna().sum()) for c in cols],
        "missing_pct": [round(float(df[c].isna().mean() * 100), 3) for c in cols],
        "non_missing_count": [int(df[c].notna().sum()) for c in cols],
        "distinct_non_missing": [int(df[c].nunique(dropna=True)) for c in cols],
    }).sort_values("missing_pct", ascending=False)

    # Per-year table: one row per year and variable, easier to filter in Excel.
    by_year = df.groupby(YEAR, dropna=False)[cols].agg(lambda s: int(s.isna().sum())).stack().rename("missing_count").reset_index()
    by_year.columns = ["year", "column", "missing_count"]
    year_sizes = df.groupby(YEAR, dropna=False).size().rename("rows_in_year").reset_index(name="rows_in_year")
    by_year = by_year.merge(year_sizes, left_on="year", right_on=YEAR if YEAR in year_sizes.columns else "year", how="left")
    by_year["missing_pct"] = (by_year["missing_count"] / by_year["rows_in_year"] * 100).round(3)
    by_year = by_year.drop(columns=[YEAR], errors="ignore")

    # Per-entity coverage; includes first/last year and count of available values per variable.
    rows = []
    for entity, group in df.groupby(ENTITY, dropna=False, sort=True):
        rec = {"entity": entity, "row_count": len(group), "first_year": group[YEAR].min(), "last_year": group[YEAR].max(),
               "distinct_years": int(group[YEAR].nunique(dropna=True))}
        for c in cols:
            if c not in (ENTITY, "Country Code", YEAR):
                rec[f"{c}__available"] = int(group[c].notna().sum())
                rec[f"{c}__missing_pct"] = round(float(group[c].isna().mean() * 100), 3)
        rows.append(rec)
    by_entity = pd.DataFrame(rows)

    # Missingness overlap for variable pairs: number of records where both exist.
    value_cols = [c for c in cols if c not in (ENTITY, "Country Code", YEAR)]
    pair_rows = []
    for a, b in combinations(value_cols, 2):
        both = df[a].notna() & df[b].notna()
        pair_rows.append({"column_a": a, "column_b": b, "rows_both_available": int(both.sum()),
                          "pct_of_all_rows_both_available": round(float(both.mean() * 100), 3),
                          "rows_a_missing_b_available": int((df[a].isna() & df[b].notna()).sum()),
                          "rows_a_available_b_missing": int((df[a].notna() & df[b].isna()).sum()),
                          "rows_both_missing": int((df[a].isna() & df[b].isna()).sum())})
    pairwise = pd.DataFrame(pair_rows).sort_values("rows_both_available", ascending=False)

    # Feasibility counts are an initial screening only; later stages validate definitions and formulas.
    feasibility = []
    for a, b, question in RESEARCH_PAIRS:
        if a in df.columns and b in df.columns:
            both = df[a].notna() & df[b].notna()
            feasibility.append({"candidate_question": question, "variable_a": a, "variable_b": b,
                                "rows_both_available": int(both.sum()),
                                "pct_of_all_rows_both_available": round(float(both.mean() * 100), 3),
                                "entities_with_at_least_one_pair": int(df.loc[both, ENTITY].nunique()),
                                "years_with_at_least_one_pair": int(df.loc[both, YEAR].nunique()),
                                "note": "Coverage screen only; not proof of conceptual validity or causality."})
    feasible = pd.DataFrame(feasibility).sort_values("rows_both_available", ascending=False)
    return overall, by_year, by_entity, pairwise, feasible

def main():
    df = load_data()
    overall, by_year, by_entity, pairwise, feasible = build_missingness_tables(df)
    overall.to_csv(OUT / "04_missingness_overall.csv", index=False)
    by_year.to_csv(OUT / "04_missingness_by_year.csv", index=False)
    by_entity.to_csv(OUT / "04_missingness_by_entity.csv", index=False)
    pairwise.to_csv(OUT / "04_pairwise_coverage.csv", index=False)
    feasible.to_csv(OUT / "04_research_pair_feasibility.csv", index=False)

    lines = [
        "STAGE 04 — MISSINGNESS PATTERN AUDIT",
        "====================================",
        f"Input: {INPUT.name} | Sheet: {SHEET}",
        f"Rows: {len(df):,} | Columns: {len(df.columns):,} | Entities: {df[ENTITY].nunique():,}",
        f"Year range: {df[YEAR].min()}–{df[YEAR].max()}",
        "",
        "HOW TO READ THIS AUDIT",
        "- Missing means blank/NA in the workbook, not zero.",
        "- Coverage counts describe the final master sheet; without source files they cannot prove why a value is absent or which join caused it.",
        "- Pairwise coverage is the number of rows where both variables exist. Actual analysis may need more filters and comparable units.",
        "- Country/entity counts include aggregates (for example, World or regions) unless filtered in later analysis.",
        "",
        "VARIABLES WITH THE MOST MISSING VALUES",
    ]
    for _, r in overall.head(12).iterrows():
        lines.append(f"- {r['column']}: {int(r['missing_count']):,}/{int(r['total_rows']):,} missing ({r['missing_pct']:.1f}%), {int(r['non_missing_count']):,} available")
    lines += ["", "CANDIDATE QUESTION COVERAGE (screening only)"]
    for _, r in feasible.iterrows():
        lines.append(f"- {r['candidate_question']}: {int(r['rows_both_available']):,} rows ({r['pct_of_all_rows_both_available']:.1f}%), {int(r['entities_with_at_least_one_pair'])} entities, {int(r['years_with_at_least_one_pair'])} years")
    lines += ["", "FILES CREATED", "- 04_missingness_overall.csv: missing/non-missing counts by column.",
              "- 04_missingness_by_year.csv: missing count and percentage per year and variable.",
              "- 04_missingness_by_entity.csv: year span and available/missing percentage per entity and variable.",
              "- 04_pairwise_coverage.csv: coverage overlap for all variable pairs.",
              "- 04_research_pair_feasibility.csv: initial coverage counts for plausible question pairs.",
              "", "No source data was edited."]
    (OUT / "04_missingness_summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print("Stage 04 complete. Reports written to", OUT)
    print("\n".join(lines[:18]))

if __name__ == "__main__":
    main()
