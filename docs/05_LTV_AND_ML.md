# 05 — Customer LTV and Machine Learning (No Leakage)

## Precise modeling task
At **day 90 after acquisition**, predict an individual customer's **next 180 days of contribution margin**, discounted to checkpoint date. This is a forward customer-value proxy, not customer lifetime value over the customer's entire existence and not a prospect-time acquisition prediction. Clearly label **Predicted 180-day Forward Customer Value (from Day 90)** and explain the horizon. Do not claim all-time LTV.

**Target:** Sum transaction contribution from `checkpoint + 1 day` through `checkpoint + 180 days` discounted monthly using configurable annual discount rate. Implement discount factor explicitly, e.g. `1 / (1 + annual_rate) ** (days_after_checkpoint / 365.25)`. The target may be negative; preserve losses and avoid blindly clipping.

## Features permitted at checkpoint
`market`, `channel`, `synthetic_segment`, pre-lead site visits/engagement, acquisition month, time since lead, offer arm (known), first-90-day transaction count, first-90-day gross revenue, first-90-day contribution, days since last transaction, average transaction size, first-90-day active months and transaction frequency. Fit preprocessing (imputation, one-hot encoding, scaling if needed) on training fold only. **No** post-checkpoint transaction info, target leakage, non-mature cohorts, simulator latent parameters or future spend.

## Splits
Chronological by **acquisition month** or checkpoint month: oldest approx 60% train, next 20% validation, latest 20% test. All entries fully matured before inclusion. Stable cohort boundaries, never split random rows from same acquired cohort across train and test. Define folds in metadata and report dates/counts. A customer is in one split only.

## Models
- Baseline: constant training median or market/channel cohort median, with robust unseen-category fallback.
- Primary: `HistGradientBoostingRegressor` with proper preprocessing or `RandomForestRegressor`; CPU-friendly and deterministic. Optional two-stage transaction/no-transaction classifier and conditional model only if it improves defensibility.
- Do a limited hyperparameter grid on temporal validation; never use test for model selection. Refit train+validation once, evaluate test once. Compare to baseline.
- Metrics: test MAE, RMSE, median absolute error, WAPE (only when denominator safely nonzero; signed targets have caveats), signed bias, segment/market errors and forecast-to-actual decile calibration; optionally prediction intervals based on validation residuals labeled approximate.
- Save fitted pipeline, feature schema, split dates, model version, seed, metrics JSON and reproducible plots. Never claim model improvement unless actual results support it.

## Reporting
A page shows model versus baseline, honest held-out metrics, feature importances (permutation on holdout or validation with caveats), predicted/actual by deciles and performance by market/segment. Include a clear paragraph: no prospective customer predictions from this model until 90 days have elapsed.

## Tests
- Input feature columns have no target/future dates, source events all <= checkpoint.
- Every label event is strictly after checkpoint and <= +180d.
- Complete maturity, no customer overlap between splits, strictly ordered splits.
- Deterministic training with fixed data/seed.
- Baseline computed only on training data, evaluation on held-out test.
- Negative outcomes preserved where economically feasible; avoid leakage from latent generator truth.
