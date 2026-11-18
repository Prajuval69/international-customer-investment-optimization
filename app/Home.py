import plotly.express as px
import streamlit as st

from app.components import (
    P,
    data,
    export,
    filters,
    financial_groups,
    header,
    money,
    nonempty,
    percent,
    plot,
    read_json,
)
from investopt.kpis import scorecard

manifest = header(
    "International acquisition & investment",
    "A reconciled view of customer growth, 180-day cohort economics and campaign investment.",
)
frame = nonempty(data(**filters()))
f = scorecard(frame)
st.caption(
    "Financial cards: complete 180-day acquisition cohorts in the selected lead months. All money is USD."
)
columns = st.columns(4)
for col, label, value in zip(
    columns,
    ["Acquired customers", "Lead conversion", "180-day contribution", "CAC incl. payouts"],
    [
        f"{f['acquisitions']:,}",
        percent(f["conversion_rate"]),
        money(f["contribution_usd"]),
        money(f["cac_usd"]),
    ],
):
    col.metric(label, value)
columns = st.columns(4)
for col, label, value in zip(
    columns,
    ["Campaign spend", "Cohort ROI", "Profit after acquisition", "Budget utilization"],
    [
        money(f["campaign_spend_usd"]),
        percent(f["cohort_roi"]),
        money(f["net_profit_usd"]),
        percent(f["utilization"]),
    ],
):
    col.metric(label, value)
trend = frame.groupby("month_start", as_index=False)[["lead_count", "converted_count"]].sum()
left, right = st.columns([1.5, 1])
with left:
    plot(
        px.line(
            trend,
            x="month_start",
            y=["lead_count", "converted_count"],
            markers=True,
            title="Lead-month growth",
            labels={"value": "Leads / acquisitions", "month_start": "Lead month"},
        )
    )
with right:
    spend = frame.groupby("market", as_index=False)[["actual_spend_usd", "planned_spend_usd"]].sum()
    plot(
        px.bar(
            spend,
            x="market",
            y=["actual_spend_usd", "planned_spend_usd"],
            barmode="group",
            title="Campaign investment by market (USD)",
        )
    )
groups = financial_groups(frame, "market")
left, right = st.columns(2)
with left:
    plot(
        px.bar(
            groups,
            x="market",
            y="cac_usd",
            title="Acquisition cost including welcome payouts",
            labels={"cac_usd": "CAC (USD)"},
        )
    )
with right:
    fig = px.bar(groups, x="market", y="cohort_roi", title="180-day acquisition-cohort ROI")
    fig.update_yaxes(tickformat=".0%")
    plot(fig)
best = groups.sort_values("net_profit_usd", ascending=False).iloc[0]
st.info(
    f"{best.market} has the highest selected synthetic cohort profit: {money(best.net_profit_usd)}. These are descriptive economics; channel spend differences do not establish causal returns."
)
reconciliation = read_json(P.artifacts / "reconciliation.json")
st.success(
    f"Reconciled: campaign spend preserved and {reconciliation['experiment_count']:,} unique randomized lead outcomes."
)
run = read_json(P.artifacts / "demo_manifest.json")
st.caption(
    f"Pipeline run UTC: {run['run_timestamp_utc']} · Seed {manifest['seed']} · Fictional events in 2024–2025"
)
with st.expander("Definitions & selected source rows"):
    st.write(
        "Contribution = revenue − direct variable costs − servicing. CAC = (spend + payouts)/acquisitions. Cohort ROI = (contribution − spend − payouts)/(spend + payouts). Undefined ratios display N/A. Maturity is conservative at campaign-month level."
    )
    st.dataframe(frame, hide_index=True)
export(frame, "campaign_cohorts")
