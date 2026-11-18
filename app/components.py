"""Shared UI, cache invalidation, scoped filters and reconciled exports."""

import json
import textwrap

import pandas as pd
import plotly.express as px
import streamlit as st

from investopt.kpis import query, scorecard
from investopt.paths import paths
from investopt.reporting import DISCLAIMER, labeled, workbook_bytes

P = paths()
COLORS = ["#087E8B", "#244D79", "#BA6A37", "#77933C", "#7A629C"]
px.defaults.color_discrete_sequence = COLORS


def header(title, description):
    st.set_page_config(page_title=f"InvestOpt | {title}", page_icon="📊", layout="wide")
    st.markdown(
        """<style>
      .block-container {padding-top:4rem; padding-bottom:3rem; max-width:1500px}
      [data-testid="stMetric"] {background:#fff; border:1px solid #DFE6EE;
        border-top:3px solid #087E8B; padding:16px; border-radius:6px}
      h1 {letter-spacing:-.035em} h2 {letter-spacing:-.02em}
      [data-testid="stMetricValue"] {font-size:clamp(1.25rem,2.3vw,2.25rem)}
      @media(max-width:900px) {
        [data-testid="stHorizontalBlock"] {flex-wrap:wrap}
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 45% !important; min-width:0}
      }
      @media(max-width:480px) {
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 100% !important}
      }
    </style>""",
        unsafe_allow_html=True,
    )
    st.caption(DISCLAIMER)
    st.title(title)
    st.write(description)
    if not P.db.exists():
        st.info("Build your local dataset: `python -m investopt demo --seed 42`")
        st.stop()
    manifest = read_json(P.raw / "manifest.json")
    st.sidebar.title("Investment intelligence")
    st.sidebar.caption(f"Synthetic seed {manifest['seed']} · USD reporting")
    st.sidebar.caption(f"Fictional observation end: {manifest['observation_end']}")
    return manifest


def read_json(file):
    if not file.exists():
        st.info(f"Missing {file.name}. Run: `python -m investopt demo --seed 42`")
        st.stop()
    return json.loads(file.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def cached_query(table, modification_ns, **kwargs):
    return query(table, root=P.root, **kwargs)


def data(table="mart_campaign_month", **kwargs):
    return cached_query(table, P.db.stat().st_mtime_ns, **kwargs)


def filters(dates=True, maturity=True):
    base = data()
    markets = sorted(base.market.unique())
    channels = sorted(base.channel.unique())
    chosen_markets = st.sidebar.multiselect(
        "Markets", markets, default=markets, key="global_markets"
    )
    chosen_channels = st.sidebar.multiselect(
        "Channels", channels, default=channels, key="global_channels"
    )
    result = {"markets": chosen_markets, "channels": chosen_channels}
    if dates:
        months = sorted(base.month_start.dt.strftime("%Y-%m-%d").unique())
        first, last = st.sidebar.select_slider(
            "Lead cohort month", months, value=(months[0], months[-1]), key="global_months"
        )
        result.update(start=first, end=last)
    if maturity:
        result["mature"] = st.sidebar.checkbox(
            "Complete 180-day cohorts only", value=True, key="global_mature"
        )
    return result


def nonempty(frame):
    if frame.empty:
        st.info("No observations match this selection. Widen the filters.")
        st.stop()
    return frame


def money(value, decimals=0):
    return "N/A" if value is None or pd.isna(value) else f"${value:,.{decimals}f}"


def percent(value):
    return "N/A" if value is None or pd.isna(value) else f"{value:.1%}"


def plot(figure):
    if figure.layout.title.text:
        title = figure.layout.title.text.replace("<br>", " ")
        figure.update_layout(
            title={"text": "<br>".join(textwrap.wrap(title, 38)), "font": {"size": 16}, "x": 0.02}
        )
    labels = {
        "lead_count": "Eligible leads",
        "converted_count": "Acquisitions",
        "actual_spend_usd": "Actual spend (USD)",
        "planned_spend_usd": "Planned spend (USD)",
        "month_start": "Lead cohort month",
        "cohort_roi": "Cohort ROI",
        "synthetic_segment": "Behavior segment",
        "contribution_180d_usd": "180-day contribution (USD)",
        "target_future_contribution_180d_usd": "Observed forward value (USD)",
        "prediction_usd": "Predicted value (USD)",
        "observed_usd": "Observed (USD)",
        "predicted_usd": "Predicted (USD)",
        "baseline_spend_usd": "Baseline spend (USD)",
        "campaign_spend_usd": "Optimized spend (USD)",
        "baseline_profit_usd": "Baseline profit (USD)",
        "optimized_profit_usd": "Optimized profit (USD)",
        "variable": "",
        "value": "USD",
        "market": "Market",
        "channel": "Channel",
        "decile": "Forecast decile",
    }
    for trace in figure.data:
        if trace.name in labels:
            trace.name = labels[trace.name]
    for axis in (figure.layout.xaxis, figure.layout.yaxis):
        if axis.title.text in labels:
            axis.title.text = labels[axis.title.text]
    figure.update_layout(
        font={"family": "Arial", "size": 13, "color": "#12233D"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 15, "r": 15, "t": 90, "b": 25},
        legend={"orientation": "h", "y": -0.2},
    )
    st.plotly_chart(figure, width="stretch")


def export(frame, name):
    left, right = st.columns(2)
    left.download_button(
        "Download filtered CSV",
        labeled(frame).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{name}.csv",
        mime="text/csv",
    )
    right.download_button(
        "Download filtered Excel",
        workbook_bytes({name: frame}),
        file_name=f"{name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def financial_groups(frame, dimension):
    return pd.DataFrame(
        [{dimension: key, **scorecard(group)} for key, group in frame.groupby(dimension)]
    )
