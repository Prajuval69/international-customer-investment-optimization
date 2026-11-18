"""Raw contracts: reject corrupt canonical inputs before building any marts."""

import json

import numpy as np
import pandas as pd

from investopt.config import write_json
from investopt.generator import TABLES
from investopt.paths import paths

REQUIRED = {
    "markets": ["market", "name", "local_currency", "usd_per_local_unit", "fx_assumption_date"],
    "campaign_budget": [
        "campaign_id",
        "market",
        "channel",
        "month_start",
        "planned_spend_usd",
        "actual_spend_usd",
        "campaign_status",
    ],
    "leads": [
        "lead_id",
        "lead_date",
        "market",
        "channel",
        "campaign_id",
        "synthetic_segment",
        "site_visits_pre_lead",
        "engagement_score_pre_lead",
        "offer_arm",
        "offer_variant",
        "converted",
        "customer_id",
        "conversion_date",
    ],
    "customers": [
        "customer_id",
        "lead_id",
        "acquisition_date",
        "market",
        "channel",
        "synthetic_segment",
        "offer_arm",
    ],
    "transactions": [
        "transaction_id",
        "customer_id",
        "txn_date",
        "gross_revenue_usd",
        "direct_variable_cost_usd",
        "servicing_cost_usd",
        "contribution_usd",
    ],
    "offer_payouts": ["payout_id", "lead_id", "payout_date", "incentive_cost_usd"],
}
KEYS = dict(
    zip(TABLES, ["market", "campaign_id", "lead_id", "customer_id", "transaction_id", "payout_id"])
)


def check_tables(tables, observation_end):
    errors, checks = [], []

    def check(condition, message):
        checks.append({"check": message, "passed": bool(condition)})
        if not condition:
            errors.append(message)

    for name, required in REQUIRED.items():
        if name not in tables or not set(required).issubset(tables[name].columns):
            raise ValueError(f"{name}: missing table or required columns {required}")
        t = tables[name]
        check(not t[KEYS[name]].duplicated().any(), f"{name}: unique primary key")
        nullable = {"customer_id", "conversion_date"} if name == "leads" else set()
        check(
            not t[[c for c in required if c not in nullable]].isna().any().any(),
            f"{name}: required values present",
        )
        for col in required:
            if col.endswith("_usd") and col != "contribution_usd" or col == "usd_per_local_unit":
                check(
                    pd.api.types.is_numeric_dtype(t[col])
                    and np.isfinite(t[col]).all()
                    and t[col].ge(0).all(),
                    f"{name}.{col}: finite nonnegative money",
                )
        for col in [c for c in required if c.endswith("_date") and c != "fx_assumption_date"] + (
            ["month_start"] if name == "campaign_budget" else []
        ):
            check(pd.api.types.is_datetime64_any_dtype(t[col]), f"{name}.{col}: datetime type")
    m, b, lead_rows, c, t, pay = [tables[n] for n in TABLES]
    if errors:
        return {
            "passed": False,
            "errors": errors,
            "checks": checks,
            "row_counts": {k: len(v) for k, v in tables.items()},
            "missingness": {k: v.isna().sum().to_dict() for k, v in tables.items()},
        }
    check(set(m.market) == {"IN", "GB", "CA", "AU", "SG"}, "five expected markets")
    check(m.usd_per_local_unit.gt(0).all(), "positive illustrative FX")
    check(not b.duplicated(["market", "channel", "month_start"]).any(), "campaign grain unique")
    for name in ["leads", "customers", "campaign_budget"]:
        check(tables[name].market.isin(m.market).all(), f"{name}: market foreign key")
        check(
            tables[name].channel.isin(["Search", "Social", "Referral", "Partnership"]).all(),
            f"{name}: channel enum",
        )
    check(lead_rows.converted.isin([0, 1]).all(), "binary conversions")
    check(lead_rows.offer_arm.isin(["treatment", "control"]).all(), "known assignment arms")
    check(
        (
            (lead_rows.offer_arm.eq("control") & lead_rows.offer_variant.eq("none"))
            | (lead_rows.offer_arm.eq("treatment") & lead_rows.offer_variant.eq("welcome_credit"))
        ).all(),
        "known offer variants",
    )
    check(
        lead_rows.engagement_score_pre_lead.between(0, 1).all()
        and lead_rows.site_visits_pre_lead.ge(0).all(),
        "valid prelead features",
    )
    converted = lead_rows[lead_rows.converted.eq(1)]
    check(
        lead_rows.customer_id.notna().equals(lead_rows.converted.eq(1))
        and lead_rows.conversion_date.notna().equals(lead_rows.converted.eq(1)),
        "conversion nullable fields consistent",
    )
    check(
        not converted.customer_id.duplicated().any() and not c.lead_id.duplicated().any(),
        "one customer per lead",
    )
    check(
        set(c.customer_id) == set(converted.customer_id)
        and set(c.lead_id) == set(converted.lead_id),
        "customers match conversions",
    )
    check(
        (converted.conversion_date - converted.lead_date).dt.days.between(0, 30).all(),
        "conversion within 30 days",
    )
    joined = lead_rows.merge(
        b, on="campaign_id", suffixes=("", "_budget"), how="left", validate="many_to_one"
    )
    check(
        joined.market_budget.notna().all()
        and joined.market.eq(joined.market_budget).all()
        and joined.channel.eq(joined.channel_budget).all()
        and joined.lead_date.dt.to_period("M").dt.to_timestamp().eq(joined.month_start).all(),
        "campaign attribution matches lead",
    )
    cj = c.merge(
        converted, on=["customer_id", "lead_id"], suffixes=("", "_lead"), validate="one_to_one"
    )
    check(
        cj.acquisition_date.eq(cj.conversion_date).all()
        and all(
            cj[x].eq(cj[x + "_lead"]).all()
            for x in ["market", "channel", "offer_arm", "synthetic_segment"]
        ),
        "customer attributes match lead",
    )
    tj = t.merge(
        c[["customer_id", "acquisition_date", "market"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )
    check(
        tj.acquisition_date.notna().all() and tj.txn_date.ge(tj.acquisition_date).all(),
        "transaction foreign key and chronology",
    )
    check(
        np.isfinite(t.contribution_usd).all()
        and np.allclose(
            t.contribution_usd,
            t.gross_revenue_usd - t.direct_variable_cost_usd - t.servicing_cost_usd,
            atol=1e-8,
        ),
        "transaction contribution reconciliation",
    )
    if "gross_revenue_local" in tj:
        check(
            np.allclose(
                tj.gross_revenue_local * tj.market.map(m.set_index("market").usd_per_local_unit),
                tj.gross_revenue_usd,
            ),
            "local to USD FX reconciliation",
        )
    pj = pay.merge(
        lead_rows[["lead_id", "offer_arm", "converted", "conversion_date"]],
        on="lead_id",
        how="left",
        validate="many_to_one",
    )
    check(
        not pay.lead_id.duplicated().any()
        and pj.converted.eq(1).all()
        and pj.offer_arm.eq("treatment").all()
        and pj.payout_date.ge(pj.conversion_date).all(),
        "payouts only converted treatment once after conversion",
    )
    end = pd.Timestamp(observation_end)
    check(
        lead_rows.lead_date.le(end).all()
        and c.acquisition_date.le(end).all()
        and t.txn_date.le(end).all()
        and pay.payout_date.le(end).all(),
        "events within observation end",
    )
    result = {
        "passed": not errors,
        "errors": errors,
        "checks": checks,
        "row_counts": {k: len(v) for k, v in tables.items()},
        "missingness": {k: v.isna().sum().to_dict() for k, v in tables.items()},
    }
    return result


def validate(root=None):
    p = paths(root).prepare()
    if not (p.raw / "manifest.json").exists():
        raise ValueError("Missing raw data. Run: python -m investopt demo --seed 42")
    manifest = json.loads((p.raw / "manifest.json").read_text())
    tables = {name: pd.read_parquet(p.raw / f"{name}.parquet") for name in TABLES}
    result = check_tables(tables, manifest["observation_end"])
    write_json(p.artifacts / "data_quality.json", result)
    (p.reports / "data_quality.md").write_text(
        "# SIMULATED DATA — Data quality\n\n"
        + "\n".join(
            f"- {'PASS' if x['passed'] else 'FAIL'}: {x['check']}" for x in result["checks"]
        ),
        encoding="utf-8",
    )
    if not result["passed"]:
        raise ValueError("Source validation failed: " + "; ".join(result["errors"]))
    return result
