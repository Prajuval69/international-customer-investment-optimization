import pandas as pd
import plotly.express as px
import streamlit as st

from app.components import P, export, filters, header, money, nonempty, plot, read_json
from investopt.ltv import TARGET, metrics

header("Customer value", "Predicted 180-day Forward Customer Value (from Day 90)")
st.info(
    "180-day post-day-90 prediction. Only information available at the day-90 checkpoint is used. This model cannot make prospect-time acquisition decisions."
)
meta = read_json(P.artifacts / "model_metrics.json")
if not (P.artifacts / "holdout_predictions.parquet").exists():
    st.info("Run: `python -m investopt train --seed 42`")
    st.stop()
scope = filters(dates=False, maturity=False)
full = pd.read_parquet(P.artifacts / "holdout_predictions.parquet")
frame = full.loc[full.market.isin(scope["markets"]) & full.channel.isin(scope["channels"])].copy()
months = sorted(full.acquisition_cohort.dt.strftime("%Y-%m-%d").unique())
chosen = st.multiselect("Held-out acquisition cohorts", months, default=months)
frame = nonempty(frame.loc[frame.acquisition_cohort.dt.strftime("%Y-%m-%d").isin(chosen)])
st.caption(
    f"Held-out period: {meta['splits']['test']['start']} to {meta['splits']['test']['end']} · selected customers N={len(frame):,}"
)
model, base = (
    metrics(frame[TARGET], frame.prediction_usd),
    metrics(frame[TARGET], frame.baseline_usd),
)
cols = st.columns(4)
for col, label, value in zip(
    cols,
    ["Model MAE", "Training-median baseline MAE", "Model RMSE", "Signed prediction bias"],
    [
        money(model["mae"], 2),
        money(base["mae"], 2),
        money(model["rmse"], 2),
        money(model["signed_bias_usd"], 2),
    ],
):
    col.metric(label, value)
st.caption(
    f"Approximate validation-residual 95% interval coverage, original full holdout: {meta['test_approx_interval_coverage']:.1%}. {meta['interval_caveat']}"
)
left, right = st.columns(2)
with left:
    plot(
        px.scatter(
            frame,
            x=TARGET,
            y="prediction_usd",
            color="market",
            opacity=0.5,
            title="Held-out observed vs predicted forward value (USD)",
            hover_data=["customer_id"],
        )
    )
with right:
    bins = frame.groupby("decile", as_index=False).agg(
        observed_usd=(TARGET, "mean"),
        predicted_usd=("prediction_usd", "mean"),
        n=("customer_id", "size"),
    )
    plot(
        px.bar(
            bins,
            x="decile",
            y=["observed_usd", "predicted_usd"],
            barmode="group",
            title="Calibration by original forecast decile (USD)",
            hover_data=["n"],
        )
    )
dimension = st.radio("Error breakdown", ["market", "synthetic_segment"], horizontal=True)
diagnostics = pd.DataFrame(
    [
        {dimension: name, "n": len(g), **metrics(g[TARGET], g.prediction_usd)}
        for name, g in frame.groupby(dimension)
    ]
)
plot(
    px.bar(
        diagnostics,
        x=dimension,
        y="mae",
        hover_data=["n", "signed_bias_usd"],
        title="Selected holdout mean absolute error (USD)",
    )
)
st.dataframe(diagnostics, hide_index=True)
importance = pd.read_csv(P.reports / "model_feature_importance.csv")
plot(
    px.bar(
        importance.sort_values("validation_mae_increase_usd"),
        x="validation_mae_increase_usd",
        y="feature",
        orientation="h",
        error_x="std_usd",
        title="Validation permutation ranking: change in MAE (USD)",
    )
)
st.caption(
    "Feature ranking uses the validation model, before final refit. Correlated features share predictive information; ranking is not causal."
)
with st.expander("Temporal splits, selection and full metrics"):
    st.dataframe(
        pd.DataFrame(
            [
                {"split": k, **{x: v[x] for x in ["n", "start", "end"]}}
                for k, v in meta["splits"].items()
            ]
        ),
        hide_index=True,
    )
    st.dataframe(pd.DataFrame(meta["validation_candidates"]), hide_index=True)
    st.json({"model": model, "baseline": base, "feature_schema": meta["features"]})
export(frame, "heldout_predictions")
