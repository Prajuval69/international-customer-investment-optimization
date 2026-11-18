import numpy as np
import pytest

from investopt.optimizer import assumptions, breakdown, response, solve


def test_response_math():
    assert response(0, 100, 10) == 0
    assert response(10, 100, 10) == pytest.approx(100 * (1 - np.exp(-1)))
    assert response(20, 100, 10) - response(10, 100, 10) < response(10, 100, 10)


def test_profit_components():
    frame = assumptions().iloc[:1]
    b = breakdown(frame, np.array([10000]))
    assert b.projected_profit_usd.iloc[0] == pytest.approx(
        b.projected_contribution_usd.iloc[0] - b.projected_payouts_usd.iloc[0] - 10000
    )


@pytest.mark.parametrize("budget", [0, 1000, 1000000, 4000000])
def test_constraints(budget):
    frame = assumptions()
    frame.loc[0, "min_spend_usd"] = min(500, budget)
    out, summary = solve(frame, budget)
    assert out.campaign_spend_usd.sum() == pytest.approx(budget, abs=0.01)
    assert (out.campaign_spend_usd >= frame.min_spend_usd - 0.01).all()
    assert (out.campaign_spend_usd <= frame.max_spend_usd + 0.01).all()
    assert summary["optimized_profit_usd"] >= summary["baseline_profit_usd"] - 0.01


@pytest.mark.parametrize("budget", [-1, 4000001])
def test_infeasible_budget(budget):
    with pytest.raises(ValueError, match="Allowed range"):
        solve(assumptions(), budget)


def test_reproducible_allocation():
    a, _ = solve(assumptions(), 1000000)
    b, _ = solve(assumptions(), 1000000)
    assert np.allclose(a.campaign_spend_usd, b.campaign_spend_usd)


def test_zero_value_high_payout():
    frame = assumptions().iloc[:1].copy()
    frame["assumed_net_contribution_per_acquisition_usd"] = 0
    frame["assumed_incentive_per_acquisition_usd"] = 1000
    _, result = solve(frame, 1000)
    assert result["optimized_profit_usd"] < -1000
