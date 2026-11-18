import numpy as np
import pytest

from investopt.kpis import query
from investopt.ltv import FEATURES, TARGET, metrics, temporal_split, train


@pytest.fixture(scope="session")
def model_result(warehouse):
    return train(42, warehouse)


def test_no_future_features(warehouse):
    df = query("mart_customer_checkpoint_90d", warehouse)
    assert (
        df.feature_max_event_date.dropna()
        .le(df.loc[df.feature_max_event_date.notna(), "checkpoint_date"])
        .all()
    )
    assert not any("future" in f or "target" in f for f in FEATURES)
    valid = df.label_min_event_date.notna()
    assert df.loc[valid, "label_min_event_date"].gt(df.loc[valid, "checkpoint_date"]).all()
    valid = df.label_max_event_date.notna()
    assert (
        (df.loc[valid, "label_max_event_date"] - df.loc[valid, "checkpoint_date"])
        .dt.days.le(180)
        .all()
    )


def test_temporal_membership(warehouse):
    df = query("mart_customer_checkpoint_90d", warehouse)
    a, b, c = temporal_split(df)
    assert a.acquisition_cohort.max() < b.acquisition_cohort.min() < c.acquisition_cohort.min()
    assert b.acquisition_cohort.max() < c.acquisition_cohort.min()
    assert not set(a.customer_id) & set(c.customer_id)
    assert all(g.mature_270d.all() and g[TARGET].notna().all() for g in [a, b, c])


def test_baseline_train_only(warehouse, model_result):
    training, _, _ = temporal_split(query("mart_customer_checkpoint_90d", warehouse))
    assert model_result["baseline_training_median_usd"] == training[TARGET].median()


def test_model_saved_and_finite(warehouse, model_result):
    import pandas as pd

    df = pd.read_parquet(warehouse / "artifacts/holdout_predictions.parquet")
    assert np.isfinite(df.prediction_usd).all()
    assert len(df) == model_result["splits"]["test"]["n"]
    assert (warehouse / "artifacts/ltv_model.joblib").stat().st_size > 100


def test_training_deterministic(warehouse, model_result):
    repeated = train(42, warehouse)
    assert repeated["model"] == model_result["model"]


def test_negative_targets_preserved():
    assert metrics([-10, -5], [-10, -5])["mae"] == 0
