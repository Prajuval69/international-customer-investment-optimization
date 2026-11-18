# 09 — CLI, Reproducible Runs and Exports

Use `python -m investopt <command>` via argparse/typer. Commands must support `--help`, clear errors and nonzero exit code on failures.

## Core commands
```
python -m investopt generate --seed 42 --leads 30000
python -m investopt validate
python -m investopt build
python -m investopt train --seed 42
python -m investopt experiment --seed 42
python -m investopt optimize --budget 1000000
python -m investopt report
python -m investopt demo --seed 42
python -m investopt smoke
streamlit run app/Home.py
```
- `generate`: canonical Parquet inputs, manifest, assumption snapshots.
- `validate`: fail fast on invalid source contracts and write data quality details.
- `build`: DuckDB ETL and materialized data marts.
- `train`: train/validate/test forward 180d value model and baseline; export model and metrics.
- `experiment`: statistically evaluate the randomized welcome-offer experiment.
- `optimize`: CLI scenario, bounds, baseline and sensitivity.
- `report`: snapshot CSV/XLSX summary and Markdown/HTML PDF optional; **PDF is not mandatory** if extra dependencies complicate offline setup.
- `demo`: run full sequence as one command, regenerating from seed; print output paths.
- `smoke`: validate required artifacts and dashboard dependencies, print row counts and reconciliation summaries, exit nonzero on violations.

## Reporting requirements
- `reports/executive_summary.md` computes actual synthetic sample KPI values, with formula, horizon and filters noted.
- `reports/kpi_scorecard.csv` by market/channel/cohort month, with cohort-maturity flag.
- `reports/experiment_summary.csv`, `reports/optimizer_allocation.csv`, `reports/model_metrics.json`, `reports/data_quality.md`.
- Optional `reports/analytics_report.xlsx` multiple sheets, accurate formulas documented and values reconciled to DuckDB.
- `artifacts/demo_manifest.json` with seed, data manifest hash, model version, CLI run date and row counts.
- Docs mention when data are generated and that reporting dates reflect **fictional events in 2024–2025**, not real-time reporting.

## Developer README content
Describe business framing, screenshots if produced, installation, commands, page descriptions, methods, parameter assumptions, checks, project limitations, seed reproducibility, no real affiliation or customer data, ethical interpretation. Provide a quick dashboard walkthrough and at least two scenario examples.

## Paths
Use relative paths resolved from project root, `Path`/environment config. Generate into `data/`, `artifacts/`, `reports/`, do not commit huge derived datasets. `gitignore` excludes caches, secrets, virtual environments, generated DB/Parquet and local data (do not require secrets, but exclude them anyway).
