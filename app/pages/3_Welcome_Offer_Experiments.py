import pandas as pd
import plotly.express as px
import streamlit as st

from app.components import data, export, filters, header, money, nonempty, percent, plot
from investopt.experiment import analyze

header(
    "Welcome-offer experiments",
    "Lead-level intention-to-treat with equal 180-day follow-up after lead assignment.",
)
scope = filters(maturity=False)
frame = nonempty(data("mart_experiment_lead_outcomes", mature=True, **scope))
result = analyze(frame)
for warning in result["warnings"]:
    st.warning(warning)
effect = result["net_itt_usd"]
cols = st.columns(4)
cols[0].metric("Net ITT / assigned lead", money(effect["effect"], 2))
cols[1].metric("Treatment / control N", f"{effect['n_treatment']:,} / {effect['n_control']:,}")
cols[2].metric(
    "Conversion lift (pp)",
    "N/A"
    if result["conversion_lift"]["effect"] is None
    else f"{result['conversion_lift']['effect'] * 100:+.2f}",
)
cols[3].metric(
    "Two-sided Welch p",
    "N/A"
    if effect["p_value"] is None
    else ("<0.0001" if effect["p_value"] < 0.0001 else f"{effect['p_value']:.4f}"),
)
if effect["ci_low"] is not None:
    st.write(
        f"**Net ITT 95% confidence interval:** USD {effect['ci_low']:.2f} to USD {effect['ci_high']:.2f} per assigned lead."
    )
    if effect["ci_low"] <= 0 <= effect["ci_high"] or effect["p_value"] >= 0.05:
        st.info(
            "The selected evidence does not establish a nonzero net offer effect at the 5% level."
        )
    else:
        st.info(
            "The interval excludes zero in this simulated population. Practical relevance and generalization remain uncertain."
        )
arm = frame.groupby("offer_arm", as_index=False).agg(
    assigned=("lead_id", "size"),
    converters=("converted", "sum"),
    net_per_lead_usd=("net_contribution_180d_usd", "mean"),
    incentive_per_lead_usd=("incentive_cost_180d_usd", "mean"),
)
left, right = st.columns(2)
with left:
    plot(
        px.bar(
            arm,
            x="offer_arm",
            y=["assigned", "converters"],
            barmode="group",
            title="Randomization → customer conversion",
        )
    )
with right:
    plot(
        px.bar(
            arm,
            x="offer_arm",
            y=["net_per_lead_usd", "incentive_per_lead_usd"],
            barmode="group",
            title="180-day economics per randomized lead (USD)",
        )
    )
dimension = st.radio("Exploratory subgroups", ["market", "channel"], horizontal=True)
rows = []
for group, part in frame.groupby(dimension):
    r = analyze(part)
    rows.append({dimension: group, **r["net_itt_usd"], "warning": "; ".join(r["warnings"])})
groups = pd.DataFrame(rows)
valid = groups.dropna(subset=["effect", "ci_low", "ci_high"]).copy()
if not valid.empty:
    valid["error_plus"] = valid.ci_high - valid.effect
    valid["error_minus"] = valid.effect - valid.ci_low
    plot(
        px.scatter(
            valid,
            x=dimension,
            y="effect",
            error_y="error_plus",
            error_y_minus="error_minus",
            title="Exploratory net ITT differences with 95% Welch intervals (USD)",
        )
    )
st.dataframe(groups, hide_index=True)
st.caption(
    "Subgroups have no multiple-comparison adjustment. Nonconverters remain in the denominator with zero outcomes. Net contribution deducts incentives once; campaign spend is excluded from the randomized comparison."
)
with st.expander("Inference, conversion uncertainty & assignment balance"):
    st.write(result["method"])
    st.json(
        {
            "conversion": result["conversion_lift"],
            "pretreatment_balance": result["balance_standardized_mean_differences"],
            "treatment_fraction": percent(result["treatment_fraction"]),
            "one_arm_strata": result["one_arm_strata"],
        }
    )
    st.write(result["caveats"])
summary = pd.DataFrame(
    [
        {
            "outcome": name,
            **result[name],
            "method": result["method"],
            "horizon": result["horizon"],
            "warnings": "; ".join(result["warnings"]),
        }
        for name in ["net_itt_usd", "conversion_lift", "incentive_cost_per_lead_usd"]
    ]
)
export(summary, "filtered_experiment")
