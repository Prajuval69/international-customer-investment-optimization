# MASTER PROMPT FOR CODEX — BUILD ENTIRE PROJECT AUTONOMOUSLY

You are a senior Python software engineer, applied data scientist, analytics engineer, experiment analyst, and Streamlit product designer. **Implement, execute, verify and document** a fully functional portfolio-grade project in this workspace, end to end, following the local `docs/*.md` specifications. This project is for an applicant to American Express Analyst – Data Science (26015352), but it is **independent and fictional**; do not claim access to Amex data, systems or proprietary methods.

## Mandatory first actions
1. Inspect the repository; read `README.md` and **every file in `docs/`** before implementing.
2. Create a brief plan (in your own internal task tracker if available) and proceed without seeking routine clarification. Resolve nonessential ambiguity by the simplest defensible implementation and document your choice.
3. Treat the docs as requirements, not suggestions. Where requirements conflict, prioritize correctness, truthful interpretation, temporal leakage prevention, offline reproducibility, then UX.
4. Do **real implementation**. Do not stop at scaffolding, pseudo-code, TODOs, stubs, or a README saying what should be built.

## Required build
- Python 3.11+; pip-installable with a version-bounded `pyproject.toml`; installable with `pip install -e '.[dev]'`.
- `investopt/` package (generator, validation, DuckDB ETL/KPI queries, customer LTV modeling, randomized-offer inference, finance accounting, constrained optimization, report export, CLI).
- `app/` polished multipage Streamlit dashboard featuring Executive Overview, Markets & Acquisition, Customer Value, Welcome Offer Experiments, Investment Optimizer, Data Quality & Methodology.
- Reproducible five-market synthetic data (India, UK, Canada, Australia, Singapore), with currencies converted using **explicit fixed illustrative exchange-rate assumptions** to USD base reporting, a seed, 24 months of activity and cross-table integrity.
- Forecasted customer 180-day forward contribution margin from a 90-day post-acquisition checkpoint, measured on time-ordered holdout versus a baseline, with appropriate uncertainty and leakage controls. Include retention propensity as optional only if robust.
- Correct randomized A/B test of welcome-offer assignment **at lead level**, with zero outcomes for non-converting leads, treatment/control sizes, intention-to-treat lift, confidence intervals, p-values, and small-sample limitations. Profit metric must deduct incremental offer costs.
- SQL-based cohort and KPI analytics with CAC, acquisition rate, investment utilization, realized contribution, ROI with precise definitions, and segment/market drilldowns.
- Scenario-based nonlinear budget optimizer with allocations across market × channel, spend bounds, overall budget conservation, diminishing returns, infeasibility diagnostics, baseline-versus-optimized objective, and sensitivity analysis; assumptions clearly labeled not causal proof.
- Dashboard with actual working filters/charts/interactions, CSV/XLSX exports where relevant, and no non-functional controls.
- CLI supporting: `generate`, `validate`, `build`, `train`, `experiment`, `optimize`, `report`, `demo`, `smoke` (see docs for args and behavior).
- Unit and integration tests with deterministic fixture seeds, including mathematical invariants, data leakage prevention, one-row-per-lead experiments, and optimization feasibility. Add CI workflow if practical, no secrets required.
- High-quality README, architecture/assumptions/methodology docs, generated sample reports and screenshots if runtime browser/screenshot tooling is available.

## Mandatory constraints
- No external API keys, paid services, remote inference, internet at runtime, external hosted data, or mandatory Docker.
- No use of real personal/financial data; do not simulate protected demographic attributes used for discriminatory allocation.
- No sklearn training/evaluation leakage; chronological train/validation/test cohorts; a strong baseline and honest metrics (even if performance is mediocre).
- No comparing cohorts with different maturity windows as if equivalent.
- No double-counting acquisition costs, incentive payouts, or revenue margins.
- No hidden generator 'true response coefficients' fed into predictive analytics; optimizer may use *independent disclosed scenario assumptions*, not pretend to have identified causal response curves.
- Do not overstate statistical significance, randomness or causality. Keep precise labels and 95% confidence intervals.
- Never hardcode dashboard KPI values. All widgets and exports must connect to warehouse/model outputs.
- Use lightweight libraries/CPU and safe default data sizes; avoid expensive installs and GPU frameworks.

## Work execution protocol
Complete phases in `docs/12_IMPLEMENTATION_SEQUENCE.md` in order. After each phase run the relevant tests and repair failures. Build tests before or alongside calculations. Keep meaningful commit-ready code, typing where useful, docstrings and exceptions.

If execution environment allows command execution, **run**:
```
python -m pip install -e '.[dev]'
python -m investopt demo --seed 42
python -m investopt smoke
pytest -q
```
Also test Streamlit startup in headless mode if possible. Do not assert a command passed without recording a real successful exit code. If dependencies/network cannot be installed, complete the implementation and give accurate setup steps and explicit blockers.

## Definition of done — all must be true
1. Fresh environment follows README and reaches a functioning demo without manual data entry.
2. The entire pipeline yields actual output artifacts and nonempty dashboard metrics from synthetic data.
3. Outputs are reproducible for fixed seeds and assumptions; tables and calculations reconcile.
4. Verified ML avoids temporal leakage and is benchmarked against a baseline.
5. RCT experiment reports treatment/control, costs, effect sizes, uncertainty and caveats.
6. Budget optimizer returns feasible, nonnegative constrained allocations with auditable objective calculations.
7. Tests pass, no stub implementations, no fabricated metrics or outcomes.
8. Clear synthetic-data labels in all views and exports; limitations are explained.

## Final report to me
Explain what you actually built, important design choices, folder tree, exact setup/run commands, test outcomes with counts, evaluation metrics read from outputs (not invented), dashboard pages, screenshot paths if made, and remaining limitations. Call out **any** requirements you could not verify. Do not end with "next steps" when implementation is still incomplete: continue iterating and fixing whenever tools permit.

Begin now by reading the documentation and then build the system.
