# Analytical methodology and lineage

**SIMULATED DATA — independent portfolio project; no American Express data.**

## Source authority and reproducibility

The master prompt and original numbered specifications govern the implementation.
The only measurement sources are generated local Parquet tables, whose required
schemas are in `investopt.validation.REQUIRED`. The raw manifest records generator
version, seed, calendar, fixed FX, row counts and source/parameter SHA256. The raw
assumption snapshot records actual configuration. The demo manifest adds operational
UTC time, source-manifest fingerprint and model version. Timestamps intentionally
change on rerun; source tables are reproducible for fixed seed/configuration.

The six sources have explicit grains: market; campaign market/channel/lead month;
randomized eligible lead; converted customer; transaction event; redeemed treatment
payout. All analytical money is USD. Synthetic local gross revenue is converted using
fixed illustrative FX; costs are generated in USD. No real PII or protected demographic
features are used. Latent activity/value variables never leave the generator.

## SQL lineage and accounting

Validation precedes a DuckDB transaction replacing sources and derived marts. Failure
rolls the transaction back. SQL files are packaged in `investopt/sql`.

- `mart_campaign_month`: preaggregate customer 180-day margin and payouts, then attach
  each campaign's spend once. Never join campaign spend through transaction rows.
- `mart_acquisition_cohort`: lead-month/market/channel/behavior-segment drilldown;
  campaign spend allocated once using eligible lead shares.
- `mart_market_month`: additive market/month campaign totals.
- `mart_experiment_lead_outcomes`: exactly one row per assigned lead, with separate
  preaggregates for transactions and incentives over fixed lead-date follow-up.
- `mart_customer_checkpoint_90d`: one row per customer, allowlisted observed features,
  target, maturity and feature/label event dates for audit.

Filters use whitelisted tables and parameterized values. Ratios are recomputed from
sums, not average subgroup rates. NULL/None means undefined. Rounding is presentation
only. Contribution = gross revenue - direct costs - servicing. Acquisition investment
= campaign spend + actual incentives. Profit = contribution - investment; ROI =
profit/investment; CAC = investment/acquisitions. Costs are deducted once. The reported
ROI is acquisition-cohort attribution, not accounting-period recognition or causality.

## Calendar and exact windows

Maximum conversion delay 30 days plus checkpoint/label follow-up 270 days requires
300 days after lead. March 31, 2025 would extend into 2026, so the generator derives
the safe lead cutoff March 6, 2025 from the December 31 observation end. Acquisitions
can extend into April. This resolves the specification inconsistency in favor of
complete follow-up. Maturity remains dynamic in SQL.

| Measurement | Included days, inclusive |
|---|---|
| Financial customer contribution | acquisition 0–180 |
| Randomized contribution/payouts | lead 0–180 |
| Model transaction features | acquisition 0–90 |
| Model label | acquisition 91–270 |
| Late-window activity proxy | acquisition 151–180 |

Campaign financial maturity conservatively requires month end +30 conversion days
+180 follow-up days. ML maturity requires acquisition +270 <= observation end. An
incomplete label stays NULL. Exact tests isolate day 0,90,91,180,181,270,271 events.
Synthetic dates are timezone-free calendar days; operational timestamps are UTC.

## Customer-value model

The feature allowlist includes market/channel/behavior segment/arm, observed pre-lead
visits/engagement, conversion delay/acquisition month, and first-checkpoint recency,
frequency, revenue, contribution, average transaction size and active calendar months.
IDs, future activity, target and audit dates are excluded.

Target = sum(contribution / (1+annual_rate)^(days_after_checkpoint/365.25)) for the
180 days strictly after checkpoint. Preserve signed losses. Training uses oldest
acquisition months, validation the next months, test the latest months, approximately
60/20/20; a month never crosses folds. One-hot encoding with unknown-category handling
and numerical median imputation are fit only within the pipeline's training data.

Three HistGradientBoosting candidates are selected by temporal validation MAE. The
selected pipeline refits on train+validation. Test is evaluated once and never used
for selection. The baseline remains the original training median. Exact periods,
counts, feature schema, candidate scores, membership, pipeline and predictions are saved.

Metrics: MAE, RMSE, median absolute error, signed bias, WAPE using absolute target
magnitudes. Forecast-decile calibration and market/segment errors expose performance
variation. Validation permutation rankings are predictive, not causal. Absolute
validation residuals give a rough marginal 95% error radius; coverage after refit is
not guaranteed and actual test coverage is reported. This is a short-horizon value
proxy available only at day 90, never a prospect-time acquisition score.

## Randomized welcome offers

Balanced seeded permutations assign treatment/control within market/channel/lead
month before conversion simulation. Each stratum's arm counts differ by at most one.
There is one treatment variant. Redemption is stochastic, not conditioned on future
realized contribution. Nonconverters have zero customer outcomes and remain in ITT.

ITT = treatment mean(net lead contribution) - control mean(net lead contribution).
Net contribution already subtracts actual payouts once. Campaign spend is excluded
from arm comparison and appears separately in cohort accounting. Follow-up is fixed
lead days 0–180 for both arms. No converter-only causal estimate is substituted.

Primary inference is unadjusted two-sided Welch with a 95% t interval and Satterthwaite
degrees of freedom, supported by balanced assignment. Statsmodels Newcombe intervals
cross-check conversion differences. No stratified estimate is claimed; one-arm strata
are counted and flagged. N<30 per arm warns, N<2 disables interval/test estimation.
Assignment fractions and pre-treatment standardized mean differences are reported.
Subgroup comparisons are exploratory without multiplicity adjustment. Simulator
effects do not generalize to real customers or advertising returns.

## Constrained budget planning

Cell response = a*(1-exp(-spend/scale)). Cell profit = response*(value_multiplier*
assumed contribution - assumed incentive) - spend. Capacity and scale must be positive,
incentives nonnegative. Expected incentives are additional to the campaign budget;
ROI denominator includes both campaign spend and expected incentive payouts.

Inputs come from independent disclosed YAML assumptions, never hidden simulation
parameters or the checkpoint model. The feasible baseline uses the latest three
months of synthetic campaign spending, normalized and water-filled within the same
bounds. Without historical data the explicit fallback is equal weighting.

SciPy SLSQP uses scaled dollars and analytic objective/equality gradients. Verify finite
results, budget equality within $0.01, all bounds and baseline objective improvement.
For nonnegative net contribution coefficients this is a concave objective; negative
coefficients can be nonconcave and no global optimum is claimed. Boundary budgets
are direct feasible allocations. Infeasibility reports the allowed interval. Sensitivity
reoptimizes at 0.8/1/1.2 contribution, leaving payouts separate.

## Validation and delivery

Smoke checks source hashes, source/warehouse row counts, spend preservation, one row
per experimental lead, required artifacts and saved-model prediction reproduction.
Tests include independent toy arithmetic, corruption, exact windows, leakage, temporal
membership, inference, constraints, exports, CLI failures and Streamlit interactions.
Browser review complements AppTest; neither establishes real-world model validity.
CSV/XLSX exports preserve filters and synthetic classification; workbook metadata states
formulas/horizons. Cache keys include warehouse modification time; model artifacts
are read from generated files. No production authentication or real data integration
is implemented. Runtime needs no internet after dependencies are installed.
