# 08 — Streamlit Dashboard and UX

## Visual style
Professional financial analytics appearance: spacious readable layout, restrained dark-blue/teal accents, high-contrast charts, no decoration-only components. Use Streamlit multipage navigation, accessible legends, descriptive chart titles, clear units, and consistent number formatting. Dashboard data must come from DuckDB/artifact files (no fixed mock KPI constants).

Every page header shows: **SIMULATED DATA — Independent portfolio demonstration; no American Express data**. All optimizer views additionally show **SCENARIO, NOT OBSERVED IMPACT**. Model panels show **180-day post-day-90 prediction** and held-out period.

## Pages and widgets

### `Home.py` — Executive Overview
- Global filters: market, channel, reporting month/cohort maturity where applicable.
- KPI cards: total acquired customers, conversion rate, acquisition cost, mature cohort 180-day contribution, CAC, cohort ROI, budget utilization (with clear per-card periods).
- Monthly lead/acquisition trend; market spend/utilization comparison; CAC and ROI comparison; key highlights from computed metrics only.
- Reconciliation status and data freshness/generated date/seed; clear caveats.

### `1_Markets_and_Acquisition.py`
- Market and channel filters, date range and maturity toggles.
- Funnel from lead to converted customers and conversion rate by cohort.
- Market/channel heatmap conversion, CAC and 180-day cohort ROI where mature.
- Campaign planned versus actual spend by month; over/underutilization outliers; CSV export of filtered aggregates.
- Guard against interpreting spend association as causal.

### `2_Customer_Value.py`
- Explain the day-90 checkpoint and next-180-days target.
- Training/validation/test split dates, row counts, held-out metrics compared with baseline.
- Predicted vs observed value scatter/binned deciles, segment and market error bar chart, signed bias; feature ranking if computed.
- Emphasize synthetic short-horizon prediction, uncertainty, no decision-time misuse.

### `3_Welcome_Offer_Experiments.py`
- Offer randomization flow: eligible -> treatment/control -> converters/observed outcomes.
- ITT net contribution per randomized lead (treatment vs control), differences and 95% confidence intervals; show sample sizes and p-value.
- Conversion-rate lift and incentive cost per assigned lead.
- Filter by market/channel with low-N warnings; overall statistical estimator and exact definitions in disclosure panel.

### `4_Investment_Optimizer.py`
- Inputs: budget slider/number box, optional inclusion/exclusion of specific market/channel, per-cell spend bounds editor if practical, expected-value multiplier and scenario selection.
- Show why budgets are infeasible and allowed bounds, do not crash.
- Display base allocation vs optimized: waterfall or grouped stacked spend chart, incremental acquisitions, expected contribution, payout costs, net profit/ROI, low/base/high sensitivity.
- Download scenario allocations as CSV/Excel with assumed response parameters and timestamps.
- Banner: results use assumed diminishing-return functions and DO NOT establish causal ROI.

### `5_Data_Quality_and_Methodology.py`
- Table counts, freshness, missingness, schema violations, referential checks and spend reconciliation.
- Data dictionary, ROI formula, randomized-test design, temporal split explanation, scenario assumptions, realistic limitations.
- Link/local reference to README / methodology; dataset seed and source parameter hashes.

## Functionality criteria
- No inert buttons, sliders, empty filter options, fake success notifications, or charts bound to static example values.
- Sensitive to nonexisting data: present `Run: python -m investopt demo --seed 42` without traceback.
- Streams cached query results with invalidation on data change; modifying filters affects KPIs and charts.
- Maintain good responsiveness with default 30k leads; aggregate SQL before charting large data.
- Exported files match dashboard filters and include synthetic disclaimer.
- If screenshots cannot be captured automatically, do not fabricate screenshot files; include manual instructions.
