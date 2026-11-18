"""Independent disclosed scenario assumptions, not causal response estimates."""

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from investopt.config import configuration, write_json
from investopt.economics import safe_ratio
from investopt.paths import paths
from investopt.warehouse import connect


def assumptions(root=None):
    cfg, _ = configuration(paths(root).root)
    opt = cfg["scenario"]["optimizer"]
    rows = []
    for i, market in enumerate(cfg["markets"]["markets"]):
        for j, channel in enumerate(cfg["scenario"]["channels"]):
            rows.append(
                {
                    "market": market["market"],
                    "channel": channel,
                    "a_max_incremental_acquisitions": opt["a_by_market"][i]
                    * opt["channel_capacity_multipliers"][j],
                    "saturation_scale_usd": opt["channel_scale_usd"][j],
                    "assumed_net_contribution_per_acquisition_usd": opt["value_by_market"][i],
                    "assumed_incentive_per_acquisition_usd": opt["incentive_by_market"][i],
                    "min_spend_usd": opt["min_spend_usd"],
                    "max_spend_usd": opt["max_spend_usd"],
                }
            )
    return pd.DataFrame(rows)


def response(spend, capacity, scale):
    return np.asarray(capacity) * (-np.expm1(-np.asarray(spend) / np.asarray(scale)))


def feasible_allocation(budget, lower, upper, weights=None):
    lower, upper = np.asarray(lower, float), np.asarray(upper, float)
    if (
        not np.isfinite(budget)
        or np.any(lower < 0)
        or np.any(lower > upper)
        or not np.isfinite(lower).all()
        or not np.isfinite(upper).all()
    ):
        raise ValueError("Bounds must be finite, nonnegative and minimum <= maximum")
    if budget < lower.sum() - 1e-6 or budget > upper.sum() + 1e-6:
        raise ValueError(
            f"Infeasible campaign budget. Allowed range: ${lower.sum():,.2f} to ${upper.sum():,.2f}"
        )
    x = lower.copy()
    remaining = budget - x.sum()
    w = np.ones(len(x)) if weights is None else np.maximum(np.asarray(weights, float), 0)
    if not np.isfinite(w).all():
        raise ValueError("Baseline weights must be finite")
    for _ in range(len(x) + 2):
        room = upper - x
        active = room > 1e-8
        if remaining <= 1e-7 or not active.any():
            break
        shares = np.where(active, w, 0)
        if shares.sum() == 0:
            shares = active.astype(float)
        addition = np.minimum(room, remaining * shares / shares.sum())
        x += addition
        remaining = budget - x.sum()
    if abs(x.sum() - budget) > 1e-5:
        raise ValueError("Could not construct feasible baseline allocation")
    return x


def breakdown(frame, spend, value_multiplier=1.0):
    result = frame.copy()
    result["campaign_spend_usd"] = spend
    result["incremental_acquisitions"] = response(
        spend, frame.a_max_incremental_acquisitions, frame.saturation_scale_usd
    )
    result["projected_contribution_usd"] = (
        result.incremental_acquisitions
        * frame.assumed_net_contribution_per_acquisition_usd
        * value_multiplier
    )
    result["projected_payouts_usd"] = (
        result.incremental_acquisitions * frame.assumed_incentive_per_acquisition_usd
    )
    result["projected_investment_usd"] = spend + result.projected_payouts_usd
    result["projected_profit_usd"] = (
        result.projected_contribution_usd - result.projected_investment_usd
    )
    return result


def solve(frame, budget, value_multiplier=1.0, weights=None):
    if frame.empty:
        raise ValueError("Select at least one active market/channel")
    frame = frame.reset_index(drop=True).copy()
    numeric = frame.select_dtypes(include="number")
    if (
        not np.isfinite(numeric).all().all()
        or value_multiplier < 0
        or not np.isfinite(value_multiplier)
    ):
        raise ValueError("Scenario parameters must be finite, value multiplier nonnegative")
    if (
        frame.a_max_incremental_acquisitions.le(0).any()
        or frame.saturation_scale_usd.le(0).any()
        or frame.assumed_incentive_per_acquisition_usd.lt(0).any()
    ):
        raise ValueError("Capacity/scale must be positive; incentives nonnegative")
    lo, hi = frame.min_spend_usd.to_numpy(float), frame.max_spend_usd.to_numpy(float)
    baseline = feasible_allocation(budget, lo, hi, weights)
    a, s = frame.a_max_incremental_acquisitions.to_numpy(), frame.saturation_scale_usd.to_numpy()
    v = (
        frame.assumed_net_contribution_per_acquisition_usd * value_multiplier
        - frame.assumed_incentive_per_acquisition_usd
    ).to_numpy()
    # Scaling spend and objective makes SLSQP stable on dollar-sized constraints.
    scale = max(float(budget), 1.0)

    def objective(z):
        b = z * scale
        return -float(np.sum(response(b, a, s) * v - b)) / scale

    def gradient(z):
        return -(a / s * np.exp(-z * scale / s) * v - 1)

    if (
        np.allclose(lo, hi)
        or budget == 0
        or abs(budget - lo.sum()) < 1e-7
        or abs(budget - hi.sum()) < 1e-7
    ):
        allocation, message = baseline, "Fixed or boundary feasible allocation"
    else:
        result = minimize(
            objective,
            baseline / scale,
            jac=gradient,
            method="SLSQP",
            bounds=list(zip(lo / scale, hi / scale)),
            constraints={
                "type": "eq",
                "fun": lambda z: z.sum() - budget / scale,
                "jac": lambda z: np.ones(len(z)),
            },
            options={"ftol": 1e-12, "maxiter": 1000},
        )
        if not result.success:
            raise ValueError(f"Optimizer failed: {result.message}")
        allocation, message = result.x * scale, str(result.message)
    if (
        abs(allocation.sum() - budget) > 0.01
        or np.any(allocation < lo - 0.01)
        or np.any(allocation > hi + 0.01)
    ):
        raise ValueError("Optimizer produced invalid constrained allocation")
    optimized = breakdown(frame, allocation, value_multiplier)
    base = breakdown(frame, baseline, value_multiplier)
    if optimized.projected_profit_usd.sum() < base.projected_profit_usd.sum() - 0.01:
        raise ValueError("Optimized objective worse than feasible baseline")
    output = optimized.copy()
    output["baseline_spend_usd"] = baseline
    output["baseline_profit_usd"] = base.projected_profit_usd.to_numpy()
    output["value_multiplier"] = value_multiplier
    output["synthetic"] = True
    output["classification"] = "SCENARIO, NOT OBSERVED IMPACT"
    output["horizon_days"] = 180
    summary = {
        "budget_usd": float(budget),
        "value_multiplier": float(value_multiplier),
        "baseline_profit_usd": float(base.projected_profit_usd.sum()),
        "optimized_profit_usd": float(optimized.projected_profit_usd.sum()),
        "incremental_acquisitions": float(optimized.incremental_acquisitions.sum()),
        "contribution_usd": float(optimized.projected_contribution_usd.sum()),
        "payouts_usd": float(optimized.projected_payouts_usd.sum()),
        "projected_roi": safe_ratio(
            optimized.projected_profit_usd.sum(), optimized.projected_investment_usd.sum()
        ),
        "solver_message": message,
        "concave_objective": bool(np.all(v >= 0)),
        "limitation": "Independent assumed response curves; campaign budget excludes additional payouts. Negative net values can make objective nonconcave; local SLSQP solution only.",
    }
    return output, summary


def recent_weights(frame, root=None):
    p = paths(root)
    if not p.db.exists():
        return None
    with connect(p.root) as con:
        recent = con.execute(
            "SELECT market,channel,sum(actual_spend_usd) AS spend FROM campaign_budget WHERE month_start >= (SELECT max(month_start)-INTERVAL 2 MONTH FROM campaign_budget) GROUP BY market,channel"
        ).df()
    return frame.merge(recent, on=["market", "channel"], how="left").spend.fillna(0).to_numpy()


def optimize(budget=1000000, root=None):
    p = paths(root).prepare()
    frame = assumptions(p.root)
    weights = recent_weights(frame, p.root)
    allocation, summary = solve(frame, budget, weights=weights)
    sensitivity = []
    for name, multiplier in [("low", 0.8), ("base", 1.0), ("high", 1.2)]:
        table, result = solve(frame, budget, multiplier, weights)
        table["scenario"] = name
        table.to_csv(p.reports / f"optimizer_{name}.csv", index=False)
        sensitivity.append({"synthetic": True, "scenario": name, **result})
    allocation["run_timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    allocation.to_csv(p.reports / "optimizer_allocation.csv", index=False)
    pd.DataFrame(sensitivity).to_csv(p.reports / "optimizer_sensitivity.csv", index=False)
    write_json(
        p.artifacts / "optimizer_results.json",
        {"synthetic": True, "summary": summary, "sensitivity": sensitivity},
    )
    return summary
