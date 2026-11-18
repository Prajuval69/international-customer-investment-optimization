"""Day-90 customer checkpoint regression with held-out chronological cohorts."""

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, median_absolute_error, root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_limits

from investopt.config import write_json
from investopt.kpis import query
from investopt.paths import paths

CATEGORICAL = ["market", "channel", "synthetic_segment", "offer_arm"]
NUMERIC = [
    "site_visits_pre_lead",
    "engagement_score_pre_lead",
    "conversion_delay_days",
    "acquisition_month",
    "txn_count_90d",
    "revenue_90d_usd",
    "contribution_90d_usd",
    "avg_transaction_90d_usd",
    "active_months_90d",
    "recency_days_90d",
]
FEATURES = CATEGORICAL + NUMERIC
TARGET = "target_future_contribution_180d_usd"


def temporal_split(frame):
    frame = frame.loc[frame.mature_270d].sort_values(["acquisition_cohort", "customer_id"])
    cohorts = sorted(frame.acquisition_cohort.unique())
    if len(cohorts) < 5 or len(frame) < 40:
        raise ValueError("Need 5 mature acquisition months and 40 customers; generate more leads")
    a, b = max(1, int(len(cohorts) * 0.6)), max(2, int(len(cohorts) * 0.8))
    b = min(b, len(cohorts) - 1)
    return [
        frame.loc[frame.acquisition_cohort.isin(values)].copy()
        for values in (cohorts[:a], cohorts[a:b], cohorts[b:])
    ]


def metrics(y, pred):
    y, pred = np.asarray(y), np.asarray(pred)
    denominator = float(np.abs(y).sum())
    return {
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(root_mean_squared_error(y, pred)),
        "median_absolute_error": float(median_absolute_error(y, pred)),
        "wape": float(np.abs(y - pred).sum() / denominator) if denominator > 0 else None,
        "signed_bias_usd": float(np.mean(pred - y)),
    }


def pipeline(seed, leaves, regularization):
    prep = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
            ("num", SimpleImputer(strategy="median"), NUMERIC),
        ]
    )
    return Pipeline(
        [
            ("preprocess", prep),
            (
                "regressor",
                HistGradientBoostingRegressor(
                    max_iter=120,
                    max_leaf_nodes=leaves,
                    l2_regularization=regularization,
                    learning_rate=0.06,
                    random_state=seed,
                    early_stopping=False,
                ),
            ),
        ]
    )


@threadpool_limits.wrap(limits=2)
def train(seed=42, root=None):
    p = paths(root).prepare()
    frame = query("mart_customer_checkpoint_90d", p.root, mature=True)
    training, validation, test = temporal_split(frame)
    if frame.customer_id.duplicated().any() or frame[TARGET].isna().any():
        raise ValueError("Invalid customer modeling grain or incomplete labels")
    candidates = []
    fitted = []
    for leaves, reg in [(7, 5.0), (15, 15.0), (7, 30.0)]:
        model = pipeline(seed, leaves, reg)
        model.fit(training[FEATURES], training[TARGET])
        pred = model.predict(validation[FEATURES])
        fitted.append(model)
        candidates.append(
            {
                "max_leaf_nodes": leaves,
                "l2_regularization": reg,
                "validation_mae": float(mean_absolute_error(validation[TARGET], pred)),
            }
        )
    selected = int(np.argmin([c["validation_mae"] for c in candidates]))
    selection_model = fitted[selected]
    val_pred = selection_model.predict(validation[FEATURES])
    # Validation residual interval is approximate after train+validation refit.
    radius = float(np.quantile(np.abs(validation[TARGET] - val_pred), 0.95))
    ranking = permutation_importance(
        selection_model,
        validation[FEATURES],
        validation[TARGET],
        scoring="neg_mean_absolute_error",
        n_repeats=3,
        random_state=seed,
    )
    importance = pd.DataFrame(
        {
            "feature": FEATURES,
            "validation_mae_increase_usd": ranking.importances_mean,
            "std_usd": ranking.importances_std,
        }
    ).sort_values("validation_mae_increase_usd", ascending=False)
    best = candidates[selected]
    final = pipeline(seed, best["max_leaf_nodes"], best["l2_regularization"])
    fit_rows = pd.concat([training, validation])
    final.fit(fit_rows[FEATURES], fit_rows[TARGET])
    prediction = final.predict(test[FEATURES])
    # Baseline intentionally frozen at original training median.
    baseline_value = float(training[TARGET].median())
    baseline = np.full(len(test), baseline_value)
    output = test[
        ["customer_id", "market", "channel", "synthetic_segment", "acquisition_cohort", TARGET]
    ].copy()
    output["prediction_usd"] = prediction
    output["baseline_usd"] = baseline
    output["approx_lower_95_usd"] = prediction - radius
    output["approx_upper_95_usd"] = prediction + radius
    output["decile"] = (
        pd.qcut(output.prediction_usd.rank(method="first"), q=min(10, len(output)), labels=False)
        + 1
    )
    output["synthetic"] = True
    output.to_parquet(p.artifacts / "holdout_predictions.parquet", index=False)
    deciles = (
        output.groupby("decile")
        .agg(
            observed_usd=(TARGET, "mean"),
            predicted_usd=("prediction_usd", "mean"),
            count=("customer_id", "size"),
        )
        .reset_index()
    )
    deciles["synthetic"] = True
    deciles.to_csv(p.reports / "model_calibration.csv", index=False)
    segment_errors = []
    for dimension in ["market", "synthetic_segment"]:
        for name, g in output.groupby(dimension):
            segment_errors.append(
                {
                    "dimension": dimension,
                    "group": name,
                    "n": len(g),
                    **metrics(g[TARGET], g.prediction_usd),
                }
            )
    pd.DataFrame(segment_errors).assign(synthetic=True).to_csv(
        p.reports / "model_segment_errors.csv", index=False
    )
    importance["synthetic"] = True
    importance.to_csv(p.reports / "model_feature_importance.csv", index=False)
    splits = {}
    for name, g in zip(["train", "validation", "test"], [training, validation, test]):
        splits[name] = {
            "n": len(g),
            "start": str(g.acquisition_cohort.min().date()),
            "end": str(g.acquisition_cohort.max().date()),
            "customer_ids": g.customer_id.tolist(),
        }
    result = {
        "synthetic": True,
        "model_version": "1.0.0",
        "seed": seed,
        "task": "180-day post-day-90 prediction",
        "features": FEATURES,
        "baseline_training_median_usd": baseline_value,
        "splits": splits,
        "validation_candidates": candidates,
        "selected_candidate": selected,
        "model": metrics(test[TARGET], prediction),
        "baseline": metrics(test[TARGET], baseline),
        "approx_interval_radius_95_usd": radius,
        "test_approx_interval_coverage": float(
            np.mean(np.abs(test[TARGET] - prediction) <= radius)
        ),
        "interval_caveat": "Absolute validation residual interval; approximate, not conditional or guaranteed after refit. Signed-target WAPE uses sum of absolute targets.",
    }
    joblib.dump(final, p.artifacts / "ltv_model.joblib")
    write_json(
        p.artifacts / "feature_schema.json", {"categorical": CATEGORICAL, "numeric": NUMERIC}
    )
    write_json(p.artifacts / "model_metrics.json", result)
    write_json(p.reports / "model_metrics.json", result)
    # Membership is stored separately to keep UI metadata readable.
    write_json(
        p.artifacts / "split_membership.json", {k: v["customer_ids"] for k, v in splits.items()}
    )
    return json.loads((p.artifacts / "model_metrics.json").read_text())
