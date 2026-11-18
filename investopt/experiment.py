"""Lead-level intention-to-treat with two-sided Welch inference."""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import confint_proportions_2indep

from investopt.config import write_json
from investopt.kpis import query
from investopt.paths import paths


def mean_effect(treatment, control):
    t, c = np.asarray(treatment, dtype=float), np.asarray(control, dtype=float)
    result = {
        "n_treatment": len(t),
        "n_control": len(c),
        "treatment_mean": float(t.mean()) if len(t) else None,
        "control_mean": float(c.mean()) if len(c) else None,
        "effect": float(t.mean() - c.mean()) if len(t) and len(c) else None,
        "ci_low": None,
        "ci_high": None,
        "p_value": None,
    }
    if min(len(t), len(c)) < 2:
        return result
    vt, vc = t.var(ddof=1) / len(t), c.var(ddof=1) / len(c)
    se = float(np.sqrt(vt + vc))
    if se == 0:
        result.update(
            ci_low=result["effect"],
            ci_high=result["effect"],
            p_value=1.0 if result["effect"] == 0 else 0.0,
        )
        return result
    df = (vt + vc) ** 2 / (vt**2 / (len(t) - 1) + vc**2 / (len(c) - 1))
    width = float(stats.t.ppf(0.975, df) * se)
    result.update(
        ci_low=result["effect"] - width,
        ci_high=result["effect"] + width,
        p_value=float(2 * stats.t.sf(abs(result["effect"]) / se, df)),
    )
    return result


def analyze(frame):
    if not frame.lead_id.is_unique:
        raise ValueError("Experimental unit must be exactly one row per lead")
    frame = frame.loc[frame.mature_180d].copy()
    if not frame.offer_arm.isin(["treatment", "control"]).all():
        raise ValueError("Unknown randomized arm")
    warnings, results = [], {}
    treatment, control = (
        frame[frame.offer_arm.eq("treatment")],
        frame[frame.offer_arm.eq("control")],
    )
    for label, col in [
        ("net_itt_usd", "net_contribution_180d_usd"),
        ("conversion_lift", "converted"),
        ("incentive_cost_per_lead_usd", "incentive_cost_180d_usd"),
        ("gross_contribution_per_lead_usd", "gross_contribution_180d_usd"),
    ]:
        results[label] = mean_effect(treatment[col], control[col])
    if min(len(treatment), len(control)) < 30:
        warnings.append("Small sample: fewer than 30 leads in an arm; estimates are unstable.")
    if len(treatment) == 0 or len(control) == 0:
        warnings.append("One arm absent; no valid treatment comparison.")
    if len(treatment) and len(control):
        lo, hi = confint_proportions_2indep(
            int(treatment.converted.sum()),
            len(treatment),
            int(control.converted.sum()),
            len(control),
            method="newcomb",
        )
        results["conversion_lift"]["newcombe_ci_low"] = float(lo)
        results["conversion_lift"]["newcombe_ci_high"] = float(hi)
    strata = (
        frame.groupby(["market", "channel", "lead_month", "offer_arm"]).size().unstack(fill_value=0)
    )
    both = strata.reindex(columns=["treatment", "control"], fill_value=0).gt(0).all(axis=1)
    single = int((~both).sum())
    if single:
        warnings.append(
            f"{single} strata have only one arm; no stratified estimate is reported. Overall Welch comparison remains unadjusted."
        )
    balance = {}
    for col in ["site_visits_pre_lead", "engagement_score_pre_lead"]:
        if min(len(treatment), len(control)) > 1:
            denom = np.sqrt((treatment[col].var() + control[col].var()) / 2)
            balance[col] = (
                float((treatment[col].mean() - control[col].mean()) / denom) if denom > 0 else None
            )
    results.update(
        {
            "synthetic": True,
            "n_leads": len(frame),
            "warnings": warnings,
            "one_arm_strata": single,
            "balance_standardized_mean_differences": balance,
            "treatment_fraction": float(len(treatment) / len(frame)) if len(frame) else None,
            "method": "Unadjusted difference in lead means, two-sided Welch t interval/test (95%); Newcombe conversion interval cross-check.",
            "horizon": "Days 0–180 after lead date, all mature randomized leads including zero nonconverters.",
            "caveats": "Campaign spend excluded from ITT; payouts deducted once. Subgroups exploratory, no multiplicity adjustment. Simulator effects do not generalize.",
        }
    )
    return results


def experiment(seed=42, root=None):
    p = paths(root).prepare()
    frame = query("mart_experiment_lead_outcomes", p.root)
    result = analyze(frame)
    result["seed"] = seed  # analytic Welch inference has no stochastic bootstrap
    rows = []
    for dim in ["overall", "market", "channel"]:
        groups = [("all", frame)] if dim == "overall" else frame.groupby(dim)
        for group, g in groups:
            analysis = analyze(g)
            for outcome in ["net_itt_usd", "conversion_lift", "incentive_cost_per_lead_usd"]:
                rows.append(
                    {
                        "synthetic": True,
                        "dimension": dim,
                        "group": group,
                        "outcome": outcome,
                        **analysis[outcome],
                        "warnings": "; ".join(analysis["warnings"]),
                        "horizon": "0–180 days after lead date",
                    }
                )
    pd.DataFrame(rows).to_csv(p.reports / "experiment_summary.csv", index=False)
    write_json(p.artifacts / "experiment_results.json", result)
    return result
