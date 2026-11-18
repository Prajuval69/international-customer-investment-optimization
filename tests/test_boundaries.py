"""Exact day boundaries independently checked against packaged SQL."""

from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pandas as pd
import pytest

import investopt


def boundary_connection(warehouse, observation_days=270):
    con = duckdb.connect()
    source = warehouse / "data/raw"
    leads = pd.read_parquet(source / "leads.parquet")
    customers = pd.read_parquet(source / "customers.parquet").head(1).copy()
    customers["acquisition_date"] = pd.Timestamp("2024-01-01")
    leads = leads.loc[leads.customer_id.eq(customers.customer_id.iloc[0])].copy()
    leads["lead_date"] = pd.Timestamp("2024-01-01")
    leads["conversion_date"] = pd.Timestamp("2024-01-01")
    days = [0, 90, 91, 180, 181, 270, 271]
    transactions = pd.DataFrame(
        {
            "customer_id": [customers.customer_id.iloc[0]] * len(days),
            "transaction_id": [f"T{i}" for i in days],
            "txn_date": pd.Timestamp("2024-01-01") + pd.to_timedelta(days, unit="D"),
            "gross_revenue_usd": [10.0] * len(days),
            "contribution_usd": [10.0] * len(days),
        }
    )
    payouts = pd.DataFrame(
        {
            "lead_id": pd.Series(dtype=str),
            "payout_date": pd.Series(dtype="datetime64[ns]"),
            "incentive_cost_usd": pd.Series(dtype=float),
        }
    )
    metadata = pd.DataFrame(
        {
            "observation_end": [datetime(2024, 1, 1) + timedelta(days=observation_days)],
            "annual_discount_rate": [0.1],
        }
    )
    for name, frame in [
        ("leads", leads),
        ("customers", customers),
        ("transactions", transactions),
        ("offer_payouts", payouts),
        ("metadata", metadata),
    ]:
        con.register("frame", frame)
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM frame")
    sql_dir = Path(investopt.__file__).parent / "sql"
    con.execute((sql_dir / "01_dimensional_model.sql").read_text())
    con.execute((sql_dir / "04_experiment_metrics.sql").read_text())
    return con


def test_checkpoint_and_label_exact_boundaries(warehouse):
    with boundary_connection(warehouse) as con:
        row = con.execute("SELECT * FROM mart_customer_checkpoint_90d").df().iloc[0]
        assert row.txn_count_90d == 2  # day 0 and day 90 only
        expected = sum(10 / 1.1 ** ((d - 90) / 365.25) for d in [91, 180, 181, 270])
        assert row.target_future_contribution_180d_usd == pytest.approx(expected)
        assert row.label_min_event_date == pd.Timestamp("2024-04-01")


def test_rct_lead_180_boundary(warehouse):
    with boundary_connection(warehouse) as con:
        assert (
            con.execute(
                "SELECT gross_contribution_180d_usd FROM mart_experiment_lead_outcomes"
            ).fetchone()[0]
            == 40
        )


def test_incomplete_labels_remain_null(warehouse):
    with boundary_connection(warehouse, observation_days=269) as con:
        assert con.execute(
            "SELECT mature_270d,target_future_contribution_180d_usd FROM mart_customer_checkpoint_90d"
        ).fetchone() == (False, None)
