import plotly.express as px
import streamlit as st

from app.components import data, export, filters, financial_groups, header, nonempty, plot

header(
    "Markets & acquisition",
    "Explore lead conversion, campaign utilization and mature customer activity.",
)
scope = filters()
frame = nonempty(data(**scope))
funnel = {
    "Stage": ["Eligible leads", "Acquired customers"],
    "Count": [frame.lead_count.sum(), frame.converted_count.sum()],
}
left, right = st.columns(2)
with left:
    plot(px.funnel(funnel, x="Count", y="Stage", title="Selected lead-to-customer funnel"))
with right:
    metric = st.selectbox(
        "Market/channel comparison",
        ["conversion_rate", "cac_usd", "cohort_roi"],
        format_func=lambda key: {
            "conversion_rate": "Conversion rate",
            "cac_usd": "CAC (USD)",
            "cohort_roi": "180-day cohort ROI",
        }[key],
    )
    groups = []
    for market, group in frame.groupby("market"):
        result = financial_groups(group, "channel")
        result["market"] = market
        groups.append(result)
    import pandas as pd

    comparison = pd.concat(groups)
    pivot = comparison.pivot(index="market", columns="channel", values=metric)
    heatmap = px.imshow(
        pivot,
        text_auto=".0%" if metric != "cac_usd" else ".1f",
        aspect="auto",
        color_continuous_scale="Teal",
        title={
            "conversion_rate": "Mature cohort conversion rate",
            "cac_usd": "Mature cohort CAC (USD)",
            "cohort_roi": "180-day cohort ROI",
        }[metric],
    )
    if metric != "cac_usd":
        heatmap.update_coloraxes(colorbar_tickformat=".0%")
    plot(heatmap)
monthly = frame.groupby("month_start", as_index=False)[
    ["actual_spend_usd", "planned_spend_usd"]
].sum()
plot(
    px.bar(
        monthly,
        x="month_start",
        y=["actual_spend_usd", "planned_spend_usd"],
        barmode="group",
        title="Planned vs actual monthly campaign spend (USD)",
    )
)
activity = (
    frame.loc[frame.mature_180d]
    .groupby(["market", "month_start"], as_index=False)[["active_days_151_180", "converted_count"]]
    .sum()
)
activity["activity_rate"] = activity.active_days_151_180 / activity.converted_count.replace(
    0, float("nan")
)
plot(
    px.line(
        activity,
        x="month_start",
        y="activity_rate",
        color="market",
        markers=True,
        title="Late-window customer activity by lead cohort",
        labels={"activity_rate": "Share of acquired customers"},
    )
)
st.caption(
    "Retention proxy: at least one transaction on acquisition days 151–180, divided by acquired customers. Fully observed cohorts only; this is activity, not a contractual retention probability."
)
cohorts = nonempty(data("mart_acquisition_cohort", **scope))
segments = cohorts.groupby("synthetic_segment", as_index=False)[
    ["lead_count", "converted_count", "contribution_180d_usd"]
].sum()
plot(
    px.bar(
        segments,
        x="synthetic_segment",
        y="contribution_180d_usd",
        title="Behavior-segment 180-day contribution (USD)",
    )
)
st.subheader("Campaign utilization exceptions")
outliers = (
    frame.assign(deviation=(frame.utilization - 1).abs())
    .sort_values("deviation", ascending=False)
    .head(15)
)
st.dataframe(
    outliers[
        [
            "market",
            "channel",
            "month_start",
            "planned_spend_usd",
            "actual_spend_usd",
            "utilization",
            "lead_count",
        ]
    ],
    hide_index=True,
)
st.caption(
    "Campaign association and attribution do not establish causal advertising uplift. Financial returns exclude incomplete cohorts."
)
export(frame, "market_acquisition")
