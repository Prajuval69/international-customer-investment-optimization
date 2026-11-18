import json

import pandas as pd
import pytest

from investopt.generator import TABLES, generate
from investopt.validation import check_tables, validate


def test_seed_reproducibility(dataset, tmp_path):
    a = json.loads((dataset / "data/raw/manifest.json").read_text())
    b = generate(42, 1500, tmp_path)
    assert a == b


def test_seed_changes(dataset, tmp_path):
    a = pd.read_parquet(dataset / "data/raw/leads.parquet")
    generate(43, 1500, tmp_path)
    assert not a.equals(pd.read_parquet(tmp_path / "data/raw/leads.parquet"))


def test_contracts(dataset):
    result = validate(dataset)
    assert result["passed"] and len(result["checks"]) > 30


def test_balanced_assignment(dataset):
    lead_rows = pd.read_parquet(dataset / "data/raw/leads.parquet")
    arms = lead_rows.groupby(["campaign_id", "offer_arm"]).size().unstack(fill_value=0)
    assert (arms.treatment - arms.control).abs().max() <= 1


@pytest.mark.parametrize("n", [0, -10, 99])
def test_invalid_volume(n, tmp_path):
    with pytest.raises(ValueError, match="100 leads"):
        generate(42, n, tmp_path)


@pytest.mark.parametrize("corruption", ["spend", "key", "margin", "date", "payout", "campaign"])
def test_corruption_detected(dataset, corruption):
    tables = {n: pd.read_parquet(dataset / f"data/raw/{n}.parquet") for n in TABLES}
    if corruption == "spend":
        tables["campaign_budget"].loc[0, "actual_spend_usd"] = -1
    elif corruption == "key":
        tables["leads"].loc[1, "lead_id"] = tables["leads"].loc[0, "lead_id"]
    elif corruption == "margin":
        tables["transactions"].loc[0, "contribution_usd"] += 100
    elif corruption == "date":
        tables["transactions"].loc[0, "txn_date"] = pd.Timestamp("2020-01-01")
    elif corruption == "payout":
        tables["offer_payouts"].loc[0, "lead_id"] = (
            tables["leads"].query("offer_arm == 'control'").iloc[0].lead_id
        )
    else:
        tables["leads"].loc[0, "channel"] = "Invalid"
    assert not check_tables(tables, "2025-12-31")["passed"]
