from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
STAGE_DIR = Path(__file__).resolve().parents[1]
INPUT = REPO_ROOT / "data" / "raw" / "master excel.xlsx"
OUT = STAGE_DIR / "reports"
SHEET = "master dataset"
ENTITY, YEAR = "Country Code", "Year"


def load_data():
    if not INPUT.exists():
        raise FileNotFoundError(f"Workbook not found: {INPUT}")
    df = pd.read_excel(INPUT, sheet_name=SHEET)
    required = [
        ENTITY, YEAR, "GDP", "GDP Growth (%)",
        "Annual CO2 emissions", "CO2 Growth (%)",
        "Decoupling Status", "Transition Risk Score"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def recalculate_growth(df, value_col):
    """Calculate percentage growth for same entity in consecutive calendar years."""
    temp = df[[ENTITY, YEAR, value_col]].copy()
    temp["_idx"] = temp.index
    temp[YEAR] = pd.to_numeric(temp[YEAR], errors="coerce")
    temp[value_col] = pd.to_numeric(temp[value_col], errors="coerce")
    temp = temp.sort_values([ENTITY, YEAR])

    prev_value = temp.groupby(ENTITY)[value_col].shift(1)
    prev_year = temp.groupby(ENTITY)[YEAR].shift(1)
    valid = (
        ((temp[YEAR] - prev_year) == 1)
        & prev_value.notna()
        & (prev_value != 0)
        & temp[value_col].notna()
    )

    temp["recalculated_growth_pct"] = np.nan
    temp.loc[valid, "recalculated_growth_pct"] = (
        (temp.loc[valid, value_col] - prev_value.loc[valid])
        / prev_value.loc[valid] * 100
    )
    return temp.set_index("_idx")["recalculated_growth_pct"].reindex(df.index)


def validate_growth(df, value_col, growth_col, prefix):
    result = df[[ENTITY, "Country Name", YEAR, value_col, growth_col]].copy()
    result["recalculated_growth_pct"] = recalculate_growth(df, value_col)
    result["existing_growth_numeric"] = pd.to_numeric(
        result[growth_col], errors="coerce"
    )
    result["difference_pp"] = (
        result["existing_growth_numeric"] - result["recalculated_growth_pct"]
    )
    result["absolute_difference_pp"] = result["difference_pp"].abs()

    both = (
        result["existing_growth_numeric"].notna()
        & result["recalculated_growth_pct"].notna()
    )
    tolerance = 0.5
    result["status"] = np.select(
        [
            both & (result["absolute_difference_pp"] <= tolerance),
            both & (result["absolute_difference_pp"] > tolerance),
            result["recalculated_growth_pct"].notna()
            & result["existing_growth_numeric"].isna(),
            result["recalculated_growth_pct"].isna()
            & result["existing_growth_numeric"].notna(),
        ],
        [
            "Close within tolerance",
            "Difference: review",
            "Existing value missing",
            "Recalculation unavailable",
        ],
        default="Both unavailable",
    )
    result.to_csv(OUT / f"{prefix}_row_comparison.csv", index=False)

    summary = pd.DataFrame([{
        "existing_column": growth_col,
        "total_rows": len(result),
        "existing_values": int(result["existing_growth_numeric"].notna().sum()),
        "recalculated_values": int(result["recalculated_growth_pct"].notna().sum()),
        "comparable_rows": int(both.sum()),
        "close_rows": int((both & (result["absolute_difference_pp"] <= tolerance)).sum()),
        "rows_to_review": int((both & (result["absolute_difference_pp"] > tolerance)).sum()),
        "mean_absolute_difference_pp": (
            result.loc[both, "absolute_difference_pp"].mean()
            if both.any() else np.nan
        ),
        "comparison_tolerance_pp": tolerance,
    }])
    summary.to_csv(OUT / f"{prefix}_summary.csv", index=False)
    return summary


def profile_decoupling(df):
    result = df[
        [ENTITY, YEAR, "GDP Growth (%)", "CO2 Growth (%)", "Decoupling Status"]
    ].copy()
    gdp = pd.to_numeric(result["GDP Growth (%)"], errors="coerce")
    co2 = pd.to_numeric(result["CO2 Growth (%)"], errors="coerce")

    # Illustrative rule only; confirm the intended definition before using it.
    conditions = [
        gdp.isna() | co2.isna(),
        (gdp > 0) & (co2 < 0),
        (gdp > 0) & (co2 >= 0) & (co2 < gdp),
        (gdp > 0) & (co2 >= gdp),
        gdp.notna() & (gdp <= 0) & co2.notna(),
    ]
    labels = [
        "Not classifiable",
        "Absolute Decoupling",
        "Relative Decoupling",
        "No Decoupling",
        "No Economic Growth",
    ]
    result["proposed_status"] = np.select(conditions, labels, default="Review")
    result.to_csv(OUT / "06_decoupling_comparison.csv", index=False)

    result["existing_status"] = result["Decoupling Status"].fillna("[MISSING]")
    counts = (
        result["existing_status"].value_counts(dropna=False)
        .rename_axis("existing_status").reset_index(name="row_count")
    )
    counts.to_csv(OUT / "06_decoupling_label_counts.csv", index=False)
    return counts


def profile_transition_risk(df):
    score = pd.to_numeric(df["Transition Risk Score"], errors="coerce")
    summary = pd.DataFrame([{
        "total_rows": len(df),
        "available_scores": int(score.notna().sum()),
        "missing_scores": int(score.isna().sum()),
        "missing_percentage": float(score.isna().mean() * 100),
        "unique_scores": int(score.nunique()),
        "minimum": score.min(),
        "median": score.median(),
        "mean": score.mean(),
        "maximum": score.max(),
        "formula_status": "Unverified; profile only",
    }])
    summary.to_csv(OUT / "06_transition_risk_profile.csv", index=False)
    return summary


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_data()
    gdp_summary = validate_growth(df, "GDP", "GDP Growth (%)", "06_gdp_growth")
    co2_summary = validate_growth(
        df, "Annual CO2 emissions", "CO2 Growth (%)", "06_co2_growth"
    )
    decoupling_counts = profile_decoupling(df)
    risk_summary = profile_transition_risk(df)

    report = [
        "STAGE 06 — DERIVED VARIABLE VALIDATION",
        "=" * 42,
        f"Rows: {len(df)}",
        f"Columns: {len(df.columns)}",
        "",
        "GDP GROWTH COMPARISON",
        gdp_summary.to_string(index=False),
        "",
        "CO2 GROWTH COMPARISON",
        co2_summary.to_string(index=False),
        "",
        "EXISTING DECOUPLING LABELS",
        decoupling_counts.to_string(index=False),
        "",
        "TRANSITION RISK PROFILE",
        risk_summary.to_string(index=False),
        "",
        "LIMITATIONS",
        "- Growth is compared only across consecutive years for the same entity.",
        "- Differences are review flags, not automatic proof of error.",
        "- Decoupling rule is illustrative and needs confirmation.",
        "- Transition Risk Score formula is unverified.",
        "- Source workbook is not modified.",
    ]
    (OUT / "06_validation_summary.txt").write_text(
        "\n".join(report), encoding="utf-8"
    )
    print("\n".join(report))
    print(f"\nReports saved to {OUT}")


if __name__ == "__main__":
    main()
