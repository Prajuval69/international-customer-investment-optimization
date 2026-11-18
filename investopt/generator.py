"""Seeded synthetic events. Latent propensities never leave this module."""

import hashlib
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.special import expit

from investopt.config import configuration, write_json
from investopt.paths import paths

TABLES = ("markets", "campaign_budget", "leads", "customers", "transactions", "offer_payouts")


def generate(seed=42, leads=30000, root=None, output=None):
    if leads < 100 or seed < 0:
        raise ValueError("Use at least 100 leads and a nonnegative seed")
    p = paths(root).prepare()
    destination = p.raw if output is None else pd.io.common.stringify_path(output)
    from pathlib import Path

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    cfg, hashes = configuration(p.root)
    s = cfg["scenario"]
    rng = np.random.default_rng(seed)
    markets = pd.DataFrame(cfg["markets"]["markets"])
    markets["fx_assumption_date"] = "synthetic baseline"
    end = pd.Timestamp(s["observation_end"])
    # March 31 + 30 + 270 extends into 2026. Derive safe lead eligibility
    # instead of trusting the specification's calendar approximation.
    effective_end = pd.Timestamp(
        min(datetime.fromisoformat(s["lead_end_date"]), end.to_pydatetime() - timedelta(days=300))
    )
    if effective_end < pd.Timestamp(s["start_date"]):
        raise ValueError("Calendar must allow 30 conversion + 270 follow-up days")
    dates = pd.date_range(s["start_date"], effective_end)
    weights = 1 + 0.2 * np.sin(dates.dayofyear.to_numpy() * 2 * np.pi / 365)
    lead_date = rng.choice(dates, leads, p=weights / weights.sum())
    market_index = rng.choice(5, leads, p=[0.3, 0.23, 0.18, 0.16, 0.13])
    channel_index = rng.choice(4, leads, p=[0.35, 0.3, 0.15, 0.2])
    frame = pd.DataFrame(
        {
            "lead_id": [f"L{i:07d}" for i in range(leads)],
            "lead_date": lead_date,
            "market": markets.market.to_numpy()[market_index],
            "channel": np.array(s["channels"])[channel_index],
            "synthetic_segment": rng.choice(["Everyday", "Travel", "Digital"], leads),
            "site_visits_pre_lead": rng.poisson(3, leads),
            "engagement_score_pre_lead": rng.beta(2, 3, leads),
        }
    )
    frame["lead_month"] = frame.lead_date.dt.to_period("M").dt.to_timestamp()
    campaigns = pd.MultiIndex.from_product(
        [markets.market, s["channels"], pd.date_range(dates[0], dates[-1], freq="MS")],
        names=["market", "channel", "month_start"],
    ).to_frame(index=False)
    campaigns["campaign_id"] = [f"B{i:05d}" for i in range(len(campaigns))]
    frame = frame.merge(
        campaigns,
        left_on=["market", "channel", "lead_month"],
        right_on=["market", "channel", "month_start"],
        validate="many_to_one",
    )
    # Balanced randomized assignment precedes all simulated outcomes.
    arms = np.full(leads, "control", dtype=object)
    for indices in frame.groupby("campaign_id", sort=True).indices.values():
        indices = rng.permutation(indices)
        arms[indices[: len(indices) // 2 + int(rng.random() < 0.5) * (len(indices) % 2)]] = (
            "treatment"
        )
    frame["offer_arm"] = arms
    frame["offer_variant"] = np.where(arms == "treatment", "welcome_credit", "none")
    # Treatment can hurt net economics: small conversion boost, costly redemption.
    probability = expit(
        -2.6
        + frame.engagement_score_pre_lead * 2
        + frame.site_visits_pre_lead * 0.06
        + np.array([0, 0.1, 0.2, 0.15])[channel_index]
        + np.array([0, 0.12, 0.03, 0.06, 0.1])[market_index]
        + 0.15 * (arms == "treatment")
    )
    frame["converted"] = (rng.random(leads) < np.clip(probability, 0.02, 0.45)).astype(int)
    converted = frame.converted.eq(1)
    count = int(converted.sum())
    frame["customer_id"] = pd.Series([None] * leads, dtype="object")
    frame.loc[converted, "customer_id"] = [f"C{i:07d}" for i in range(count)]
    frame["conversion_date"] = pd.NaT
    frame.loc[converted, "conversion_date"] = frame.loc[converted, "lead_date"] + pd.to_timedelta(
        rng.integers(0, 31, count), unit="D"
    )
    customers = (
        frame.loc[
            converted,
            [
                "customer_id",
                "lead_id",
                "conversion_date",
                "market",
                "channel",
                "synthetic_segment",
                "offer_arm",
            ],
        ]
        .rename(columns={"conversion_date": "acquisition_date"})
        .reset_index(drop=True)
    )
    tx_records = []
    fx = markets.set_index("market").usd_per_local_unit.to_dict()
    for row in customers.itertuples(index=False):
        # Customer-specific latent activity, unobserved by analytics.
        rate = rng.gamma(2.3, 1.1)
        value = rng.lognormal(2.9, 0.55)
        churn_day = int(rng.exponential(430))
        max_days = min((end - row.acquisition_date).days, churn_day)
        n = int(rng.poisson(rate * (max_days + 1) / 30))
        if n == 0:
            continue
        offsets = np.sort(rng.integers(0, max_days + 1, n))
        gross = rng.lognormal(np.log(value), 0.6, n)
        # Explicit local-currency -> USD conversion; fixed assumptions only.
        gross_local = gross / fx[row.market]
        gross = gross_local * fx[row.market]
        direct = gross * rng.uniform(0.22, 0.55, n)
        service = rng.uniform(1.5, 7.5, n)
        tx_records.extend(
            zip(
                [row.customer_id] * n,
                row.acquisition_date + pd.to_timedelta(offsets, unit="D"),
                gross_local,
                gross,
                direct,
                service,
                gross - direct - service,
            )
        )
    transactions = pd.DataFrame(
        tx_records,
        columns=[
            "customer_id",
            "txn_date",
            "gross_revenue_local",
            "gross_revenue_usd",
            "direct_variable_cost_usd",
            "servicing_cost_usd",
            "contribution_usd",
        ],
    )
    transactions.insert(0, "transaction_id", [f"T{i:09d}" for i in range(len(transactions))])
    eligible = frame.loc[converted & frame.offer_arm.eq("treatment")]
    eligible = eligible.loc[rng.random(len(eligible)) < 0.78]
    payouts = eligible[["lead_id", "conversion_date", "market"]].copy()
    payouts["payout_date"] = payouts.conversion_date + pd.to_timedelta(
        rng.integers(0, 31, len(payouts)), unit="D"
    )
    payouts["incentive_cost_usd"] = payouts.market.map(
        dict(zip(markets.market, [35, 60, 50, 48, 55]))
    ).astype(float)
    payouts["payout_id"] = [f"P{i:07d}" for i in range(len(payouts))]
    payouts = payouts[["payout_id", "lead_id", "payout_date", "incentive_cost_usd"]]
    volume = frame.groupby("campaign_id").size()
    campaigns["planned_spend_usd"] = campaigns.campaign_id.map(volume).fillna(0) * rng.uniform(
        1.8, 3.4, len(campaigns)
    )
    campaigns["actual_spend_usd"] = campaigns.planned_spend_usd * rng.uniform(
        0.75, 1.28, len(campaigns)
    )
    campaigns["campaign_status"] = "complete"
    frame = frame.drop(columns=["lead_month", "month_start"])
    tables = dict(zip(TABLES, [markets, campaigns, frame, customers, transactions, payouts]))
    fingerprints = {}
    for name, table in tables.items():
        file = destination / f"{name}.parquet"
        table.to_parquet(file, index=False)
        fingerprints[name] = hashlib.sha256(file.read_bytes()).hexdigest()
    manifest = {
        "synthetic": True,
        "generator_version": "1.0.0",
        "seed": seed,
        "start_date": s["start_date"],
        "lead_end_date": str(effective_end.date()),
        "configured_lead_end_date": s["lead_end_date"],
        "observation_end": s["observation_end"],
        "row_counts": {k: len(v) for k, v in tables.items()},
        "parameter_hashes": hashes,
        "table_hashes": fingerprints,
        "fx_assumptions": markets.to_dict("records"),
        "campaign_spend_usd": float(campaigns.actual_spend_usd.sum()),
    }
    write_json(destination / "manifest.json", manifest)
    write_json(destination / "assumptions.json", cfg)
    return manifest
