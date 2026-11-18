# International acquisition & investment — synthetic executive report

SIMULATED DATA — Independent portfolio demonstration; no American Express data

Generated UTC: 2026-10-25T03:40:00.075964+00:00. Filters: all five markets,
four channels, all generated lead-month cohorts. Fictional activity: 2024–2025.
Financial results below use complete 180-day acquisition cohorts; campaign spend
is attributed to lead month, not calendar revenue recognition.

| Measure | Actual synthetic result |
|---|---:|
| Eligible leads | 30,000 |
| Acquisitions | 6,087 |
| Conversion rate | 20.29% |
| Campaign spend | $80,404.07 |
| Actual welcome payouts | $119,772.00 |
| Contribution, acquisition days 0–180 | $834,801.90 |
| CAC including payouts | $32.89 |
| Cohort acquisition ROI | 317.03% |
| Investment utilization | 102.37% |

Contribution = transaction revenue - direct variable costs - servicing costs.
Acquisition investment = campaign spend + actual welcome payouts.
Net profit = contribution - acquisition investment; ROI = net profit / investment.
Rates are recomputed from sums, not averaged subgroup rates.

## Day-90 checkpoint model

Predict next 180-day contribution discounted at the configured annual rate.
Held-out test MAE: $79.91; frozen training-median baseline
MAE: $104.68. Test RMSE: $140.87.
Test acquisition cohorts: 2025-01-01 through 2025-04-01.
Selection uses temporal validation only; preprocessing is fitted within each training fold.
This short-horizon value proxy cannot support prospect-time decisions.
Prediction intervals use validation absolute residuals and are approximate after refit.

## Randomized welcome offer

Treatment N=15,008; control N=14,992.
Net ITT/eligible lead: $-4.87, 95% Welch CI
[$-6.95, $-2.79], two-sided p=0.0000.
Includes zero outcomes for nonconverters; subtracts paid incentives once.
Follow-up is days 0–180 after lead date. Campaign spend excluded from arm comparison.
Subgroups are exploratory with no multiple-comparison adjustment.
Effects are simulator-dependent, with no inference to real customer behavior.

## Budget scenario — NOT OBSERVED IMPACT

Campaign budget: $1,000,000.00; additional expected incentives:
$319,114.46. Feasible recent-spend-weighted baseline projected profit:
$1,842,371.29; optimized projected profit: $1,911,035.43.
All results depend on independent YAML response assumptions, not causal estimates.
The optimizer never consumes post-day-90 ML predictions. Fixed spend conservation
can force negative projected returns under adverse assumptions.

## Reproducibility and limitations

See raw manifest for seed, table hashes and fixed illustrative FX; demo manifest
for run time and source fingerprint. No real customer data or Amex affiliation.
Synthetic maturity and accounting are explicit; no underwriting, credit scoring,
production authentication, live FX, or real causal marketing response claims.
