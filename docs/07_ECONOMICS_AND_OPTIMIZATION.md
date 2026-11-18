# 07 — Financial Definitions and Budget Optimization

## Accounting definitions — no double counting
Define:
- `C` = customer transaction **contribution margin** within a specified mature observation window = gross revenue minus direct variable and servicing costs.
- `S` = advertising/campaign spend, already actual dollars, excluding welcome incentives.
- `I` = actual paid welcome incentive cost in that window, distinct from campaign spend.
- `NetProfitAfterAcquisitionCosts = C - S - I` for the aligned cohort.
- `AcquisitionInvestment = S + I`.
- `CohortAcquisitionROI = (C - S - I) / (S + I)` when `S+I>0`, else N/A.
- `CAC = (S + I) / number_of_acquired_customers` for a documented cohort/window; zero denominator => N/A.
- `LTV_to_CAC` for mature cohorts only and with **matching value horizon**; if numerator is contribution per customer, denominator cost per acquisition; label as 180-day ratio. Never combine 90-day checkpoint future customer value with prospect-time CAC silently.
- `Utilization = actual_spend / planned_spend`, when planned > 0; can exceed 100%, display as such.
- `ConversionRate = converted leads / total eligible leads`.
All money in USD after illustrative fixed FX, no rounding before arithmetic. No 0-divide output `inf`/`NaN` shown to users; display N/A with explanation.

## Experiment economics vs overall ROI
ITT difference in lead net contribution already excludes incentive payouts. Do not subtract them twice when constructing an offer-lift recommendation. The RCT does not directly estimate incremental causal returns of advertising spend. Distinguish offer intervention effects from channel budget allocation assumptions.

## Optimizer design
User specifies `budget_usd` to allocate across active `market × channel` cells. Scenario response curves are **hypothetical planning assumptions**, not identified/causally fitted on observational channel data. Each cell i has assumptions:
- `a_i`: saturation count of **incremental** acquisitions over the scenario horizon, positive.
- `s_i`: dollars at e-fold saturation (response scale), positive.
- `v_i`: assumed 180-day margin contribution per *incremental* acquired customer, excluding campaign spend/incentive payout.
- `q_i`: expected offer payout per *incremental* acquisition, nonnegative.
- `min_i`, `max_i`: feasible spend bounds.

Example response and cell profit:
```
customers_i(b) = a_i * (1 - exp(-b/s_i))
profit_i(b) = customers_i(b) * (v_i - q_i) - b
```
Users can edit total budget, upper/lower bounds and an uncertainty haircut on value or returns. Document horizon and scenario parameters, avoid claiming parameter estimation from real causal data. For optimizer, *do not* directly use the 90-day-checkpoint LTV model, because the checkpoint info is unavailable at lead purchase time. Optional historical fully matured cohort averages may inform suggested v_i but still are **descriptive observational proxies**, not causal results; defaults should be disclosed YAML assumptions.

### Constraints
- `sum_i b_i = user_budget_usd` (if budget is allocated by fixed spend constraint; explain that spend conservation can make expected net profit negative in unfavorable scenarios).
- `min_i <= b_i <= max_i`, `b_i >= 0` for every active market/channel. Preserve inactive regions as zero.
- Detect budget `<sum(min)` or `>sum(max)` and raise a friendly validation error with available feasible range; never silently violate constraints.
- Optional market cap constraints can be added only with full tests and clear UI.

### Optimization method
Use `scipy.optimize.minimize(method='SLSQP')` with negative total expected net profit and analytic gradients when practical. Start from a feasible budget allocation, e.g. clip baseline or water-fill to meet bounds. Verify success with tolerance, feasibility, finite objective. For mathematically concave curves where `(v_i-q_i)>0`, this is a concave maximization under linear constraints; for `v_i-q_i<=0` still a sensible constrained objective but document interpretation. Implement a feasible equal/weighted baseline and compare optimized net profit to baseline under **the same assumptions**. Always show incremental customers, spend, expected margin, incentive costs, net profit, ROI and differences. Currency USD, costs explicit.

### Sensitivity/robustness
For low/base/high value scenarios (e.g. 0.8x/1x/1.2x net margin assumptions) rerun optimizer and show allocation/profit deltas; use safe user-controlled sliders. Can incorporate spend curve scale sensitivity. Never imply optimizer is evidence of actual causal impact.

### Unit tests (must-have)
- Closed-form single-cell response values and monotonic saturation.
- Profit objective reconciliation with components.
- Solutions obey sum spend, min/max and nonnegative within stated tolerance.
- Infeasible budget emits actionable error.
- Same assumptions/seed yield same solution.
- Optimized profit is not worse than feasible baseline beyond numeric tolerance.
- Increased spend exhibits diminishing marginal acquisition response (derivative decreases).
- Correct handling of zero contribution and high payout assumptions.
