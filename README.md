# GreenPulse — Green Transition & Economic Resilience Monitor

A data science project for auditing a master country-year dataset, validating its structure and derived variables, and exploring green transition and economic resilience through a Streamlit dashboard.

## Repository layout

- `app.py` — Streamlit dashboard.
- `data/raw/master excel.xlsx` — the single shared source workbook used by the dashboard and audit scripts.
- `audits/stage-01-workbook-inventory/` — workbook inventory script and report.
- `audits/stage-02-column-semantics/` — available column-semantics reports; the source script still needs to be added from the original Stage 2 folder.
- `audits/stage-03-data-quality/` — data-quality audit script and available reports.
- `audits/stage-04-missingness/` — missingness audit script and reports.
- `audits/stage-05-merge-validation/` — key and structural validation script and reports.
- `audits/stage-06-derived-variable-validation/` — derived-variable validation script and reports.

Earlier-stage copies of scripts, reports, and the workbook were not kept repeatedly in every stage folder. The unique stage outputs are kept with their stage; the master workbook is stored once. See `REPOSITORY_GAPS.md` for items not present in the uploaded archives.

## Setup

Use Python 3.10 or newer, then install dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard from the repository root:

```bash
streamlit run app.py
```

Audit scripts should also be run from the repository root. For example:

```bash
python audits/stage-01-workbook-inventory/src/01_workbook_inventory.py
python audits/stage-03-data-quality/src/03_data_quality_audit.py
python audits/stage-04-missingness/src/04_missingness_patterns.py
python audits/stage-05-merge-validation/src/05_merge_validation.py
python audits/stage-06-derived-variable-validation/src/06_derived_variable_validation.py
```

The audit scripts read the source workbook and write reports into their respective stage folders. They are intended to be read-only with respect to the Excel workbook. Re-run scripts only when you intend to regenerate their reports.
