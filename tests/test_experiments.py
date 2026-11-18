import numpy as np
import pandas as pd
import pytest

from investopt.experiment import analyze, mean_effect
from investopt.kpis import query


def test_hand_itt():
    x = mean_effect([0, 20, 40, 0], [0, 10, 10, 0])
    assert x["effect"] == 10 and x["n_treatment"] == 4
    assert x["ci_low"] < x["effect"] < x["ci_high"]
    assert 0 <= x["p_value"] <= 1


def test_zero_variance():
    assert mean_effect([0, 0], [0, 0])["p_value"] == 1


def test_low_n():
    assert mean_effect([1], [0])["ci_low"] is None


def test_primary_denominator(warehouse):
    f = query("mart_experiment_lead_outcomes", warehouse)
    r = analyze(f)
    assert r["n_leads"] == len(f)
    assert r["net_itt_usd"]["n_treatment"] + r["net_itt_usd"]["n_control"] == len(f)
    assert f.loc[f.offer_arm.eq("control"), "incentive_cost_180d_usd"].eq(0).all()
    assert np.allclose(
        f.gross_contribution_180d_usd - f.incentive_cost_180d_usd, f.net_contribution_180d_usd
    )


def test_duplicate_units_rejected(warehouse):
    f = query("mart_experiment_lead_outcomes", warehouse)
    with pytest.raises(ValueError, match="one row"):
        analyze(pd.concat([f, f.iloc[:1]]))


def test_single_arm_diagnostic(warehouse):
    f = query("mart_experiment_lead_outcomes", warehouse)
    r = analyze(f[f.offer_arm.eq("control")])
    assert r["one_arm_strata"] > 0 and r["warnings"]
    assert r["net_itt_usd"]["effect"] is None


def test_order_invariant(warehouse):
    f = query("mart_experiment_lead_outcomes", warehouse)
    a, b = analyze(f), analyze(f.sample(frac=1, random_state=2))
    assert a["n_leads"] == b["n_leads"]
    assert a["net_itt_usd"]["effect"] == pytest.approx(b["net_itt_usd"]["effect"])
