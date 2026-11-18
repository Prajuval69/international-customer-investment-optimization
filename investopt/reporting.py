"""Reconciled local CSV, XLSX, Markdown and standalone Plotly reports."""

import io
import json
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px

from investopt.kpis import query, scorecard
from investopt.paths import paths

DISCLAIMER = "SIMULATED DATA — Independent portfolio demonstration; no American Express data"


def labeled(frame):
    result = frame.copy()
    result["data_classification"] = DISCLAIMER
    return result


def workbook_bytes(tables):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(
            {
                "methodology": [
                    DISCLAIMER,
                    "Fictional activity in 2024–2025. USD fixed illustrative FX.",
                    "Cohort ROI = (contribution - spend - payouts)/(spend + payouts).",
                    "Customer contribution: acquisition days 0–180; RCT: lead days 0–180.",
                    "Model: day-90 checkpoint, next 180-day discounted contribution.",
                    "Optimizer: assumed curves; campaign budget excludes additional payouts.",
                ]
            }
        ).to_excel(writer, sheet_name="Read me", index=False)
        for name, frame in tables.items():
            labeled(frame).to_excel(writer, sheet_name=name[:31], index=False)
    return buffer.getvalue()


def report(root=None):
    p = paths(root).prepare()
    campaign = query(root=p.root)
    cohort = query("mart_acquisition_cohort", p.root)
    for frame, file in [(campaign, "kpi_scorecard.csv"), (cohort, "segment_cohorts.csv")]:
        labeled(frame).to_csv(p.reports / file, index=False)
    kpi = scorecard(campaign)
    model = json.loads((p.artifacts / "model_metrics.json").read_text())
    experiment = json.loads((p.artifacts / "experiment_results.json").read_text())
    opt = json.loads((p.artifacts / "optimizer_results.json").read_text())["summary"]
    effect = experiment["net_itt_usd"]
    summary = f"""# International acquisition & investment — synthetic executive report

{DISCLAIMER}

Generated UTC: {datetime.now(timezone.utc).isoformat()}. Filters: all five markets,
four channels, all generated lead-month cohorts. Fictional activity: 2024–2025.
Financial results below use complete 180-day acquisition cohorts; campaign spend
is attributed to lead month, not calendar revenue recognition.

| Measure | Actual synthetic result |
|---|---:|
| Eligible leads | {kpi["leads"]:,} |
| Acquisitions | {kpi["acquisitions"]:,} |
| Conversion rate | {kpi["conversion_rate"]:.2%} |
| Campaign spend | ${kpi["campaign_spend_usd"]:,.2f} |
| Actual welcome payouts | ${kpi["payouts_usd"]:,.2f} |
| Contribution, acquisition days 0–180 | ${kpi["contribution_usd"]:,.2f} |
| CAC including payouts | ${kpi["cac_usd"]:,.2f} |
| Cohort acquisition ROI | {kpi["cohort_roi"]:.2%} |
| Investment utilization | {kpi["utilization"]:.2%} |

Contribution = transaction revenue - direct variable costs - servicing costs.
Acquisition investment = campaign spend + actual welcome payouts.
Net profit = contribution - acquisition investment; ROI = net profit / investment.
Rates are recomputed from sums, not averaged subgroup rates.

## Day-90 checkpoint model

Predict next 180-day contribution discounted at the configured annual rate.
Held-out test MAE: ${model["model"]["mae"]:.2f}; frozen training-median baseline
MAE: ${model["baseline"]["mae"]:.2f}. Test RMSE: ${model["model"]["rmse"]:.2f}.
Test acquisition cohorts: {model["splits"]["test"]["start"]} through {model["splits"]["test"]["end"]}.
Selection uses temporal validation only; preprocessing is fitted within each training fold.
This short-horizon value proxy cannot support prospect-time decisions.
Prediction intervals use validation absolute residuals and are approximate after refit.

## Randomized welcome offer

Treatment N={effect["n_treatment"]:,}; control N={effect["n_control"]:,}.
Net ITT/eligible lead: ${effect["effect"]:.2f}, 95% Welch CI
[${effect["ci_low"]:.2f}, ${effect["ci_high"]:.2f}], two-sided p={effect["p_value"]:.4f}.
Includes zero outcomes for nonconverters; subtracts paid incentives once.
Follow-up is days 0–180 after lead date. Campaign spend excluded from arm comparison.
Subgroups are exploratory with no multiple-comparison adjustment.
Effects are simulator-dependent, with no inference to real customer behavior.

## Budget scenario — NOT OBSERVED IMPACT

Campaign budget: ${opt["budget_usd"]:,.2f}; additional expected incentives:
${opt["payouts_usd"]:,.2f}. Feasible recent-spend-weighted baseline projected profit:
${opt["baseline_profit_usd"]:,.2f}; optimized projected profit: ${opt["optimized_profit_usd"]:,.2f}.
All results depend on independent YAML response assumptions, not causal estimates.
The optimizer never consumes post-day-90 ML predictions. Fixed spend conservation
can force negative projected returns under adverse assumptions.

## Reproducibility and limitations

See raw manifest for seed, table hashes and fixed illustrative FX; demo manifest
for run time and source fingerprint. No real customer data or Amex affiliation.
Synthetic maturity and accounting are explicit; no underwriting, credit scoring,
production authentication, live FX, or real causal marketing response claims.
"""
    (p.reports / "executive_summary.md").write_text(summary, encoding="utf-8")
    tables = {
        "KPI scorecard": campaign,
        "Segment cohorts": cohort,
        "Experiment": pd.read_csv(p.reports / "experiment_summary.csv"),
        "Optimizer": pd.read_csv(p.reports / "optimizer_allocation.csv"),
        "Sensitivity": pd.read_csv(p.reports / "optimizer_sensitivity.csv"),
        "Calibration": pd.read_csv(p.reports / "model_calibration.csv"),
    }
    (p.reports / "analytics_report.xlsx").write_bytes(workbook_bytes(tables))
    trend = campaign.groupby("month_start", as_index=False)[["lead_count", "converted_count"]].sum()
    px.line(
        trend,
        x="month_start",
        y=["lead_count", "converted_count"],
        title="SIMULATED DATA — Lead and acquisition cohorts",
    ).write_html(p.reports / "acquisition_trend.html", include_plotlyjs=True)
    calibration = tables["Calibration"]
    px.bar(
        calibration,
        x="decile",
        y=["observed_usd", "predicted_usd"],
        barmode="group",
        title="SIMULATED DATA — Held-out forward-value calibration",
    ).write_html(p.reports / "model_calibration.html", include_plotlyjs=True)
    effects = (
        tables["Experiment"].query("outcome == 'net_itt_usd'").dropna(subset=["ci_low", "ci_high"])
    )
    effects = effects.assign(
        error_plus=effects.ci_high - effects.effect, error_minus=effects.effect - effects.ci_low
    )
    px.scatter(
        effects,
        x="group",
        y="effect",
        error_y="error_plus",
        error_y_minus="error_minus",
        color="dimension",
        title="SIMULATED DATA — Net offer ITT/lead and 95% Welch intervals (USD)",
    ).write_html(p.reports / "experiment_effects.html", include_plotlyjs=True)
    return {
        "report": str(p.reports / "executive_summary.md"),
        "workbook": str(p.reports / "analytics_report.xlsx"),
    }
