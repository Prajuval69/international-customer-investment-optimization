from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components import P, export, filters, header, money, percent, plot
from investopt.optimizer import assumptions, recent_weights, solve

header(
    "Investment optimizer",
    "Allocate a campaign budget under explicit hypothetical response assumptions.",
)
st.warning(
    "SCENARIO, NOT OBSERVED IMPACT — Assumed diminishing returns do not establish causal marketing ROI. Campaign budget excludes additional incentive payouts."
)
scope = filters(dates=False, maturity=False)
all_cells = assumptions(P.root)
cells = all_cells.loc[
    all_cells.market.isin(scope["markets"]) & all_cells.channel.isin(scope["channels"])
].copy()
if cells.empty:
    st.info("Select at least one active market and channel.")
    st.stop()
left, right = st.columns(2)
budget = left.number_input("Campaign budget (USD)", min_value=0.0, value=1000000.0, step=10000.0)
multiplier = right.slider(
    "Assumed contribution multiplier", min_value=0.0, max_value=1.5, value=1.0, step=0.05
)
st.caption(
    "Response = a × (1 − exp(−spend/scale)). Expected profit = acquisitions × (assumed contribution − expected incentive) − spend. Horizon: 180 days."
)
st.subheader("Editable scenario assumptions & constraints")
edited = st.data_editor(
    cells, hide_index=True, disabled=["market", "channel"], width="stretch", key="scenario_editor"
)
st.caption(
    f"Allowed campaign budget: USD {edited.min_spend_usd.sum():,.0f} to USD {edited.max_spend_usd.sum():,.0f}. Excluded cells receive zero allocation."
)
try:
    weights = recent_weights(edited, P.root)
    allocation, result = solve(edited, budget, multiplier, weights)
    sensitivity_rows, sensitivity_allocations = [], []
    for name, factor in [("low", 0.8), ("base", 1.0), ("high", 1.2)]:
        table, summary = solve(edited, budget, multiplier * factor, weights)
        sensitivity_rows.append({"scenario": name, **summary})
        table["scenario"] = name
        sensitivity_allocations.append(table)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
cols = st.columns(4)
cols[0].metric(
    "Optimized projected profit",
    money(result["optimized_profit_usd"]),
    delta=money(result["optimized_profit_usd"] - result["baseline_profit_usd"]),
)
cols[1].metric("Baseline projected profit", money(result["baseline_profit_usd"]))
cols[2].metric("Expected incremental customers", f"{result['incremental_acquisitions']:,.1f}")
cols[3].metric("Projected acquisition ROI", percent(result["projected_roi"]))
st.caption(
    (
        f"Campaign spend: {money(budget)} + expected incentives: {money(result['payouts_usd'])}; expected contribution: {money(result['contribution_usd'])}. Baseline uses normalized most recent three months of synthetic spend, adjusted to the same bounds."
    ).replace("$", r"\$")
)
allocation["cell"] = allocation.market + " / " + allocation.channel
plot(
    px.bar(
        allocation,
        x="cell",
        y=["baseline_spend_usd", "campaign_spend_usd"],
        barmode="group",
        title="Baseline vs optimized campaign allocation (USD)",
    )
)
sens = pd.DataFrame(sensitivity_rows)
plot(
    px.bar(
        sens,
        x="scenario",
        y=["baseline_profit_usd", "optimized_profit_usd"],
        barmode="group",
        title="Reoptimized value sensitivity: 0.8× / 1.0× / 1.2× selected multiplier",
    )
)
st.dataframe(
    sens[
        [
            "scenario",
            "value_multiplier",
            "incremental_acquisitions",
            "contribution_usd",
            "payouts_usd",
            "optimized_profit_usd",
            "projected_roi",
        ]
    ],
    hide_index=True,
)
with st.expander("Allocation sensitivity & objective audit"):
    st.dataframe(pd.concat(sensitivity_allocations), hide_index=True)
    st.json(result)
st.dataframe(allocation, hide_index=True)
st.caption(
    "These are independent YAML assumptions, not fitted response curves. The day-90 model is never used for acquisition-time allocation. Adverse values can produce negative profit; nonconcave cases provide a local solution only."
)


allocation["run_timestamp_utc"] = datetime.now(timezone.utc).isoformat()
export(allocation, "scenario_allocation")
