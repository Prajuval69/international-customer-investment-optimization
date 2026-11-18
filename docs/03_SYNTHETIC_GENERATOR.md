# 03 — Deterministic Synthetic Data Generation

## Generator contract
`python -m investopt generate --seed 42 --leads 30000 --output data/raw/`
Must produce Parquet raw tables and seed/parameter manifest. `--leads` default 30000; `--seed` default 42; optional `--small` / `--leads 1500` for unit and smoke tests. Deterministic for same seed and parameter file (including stable row order). Default should fit a typical laptop without GPU. Avoid global RNG; use `numpy.random.default_rng(seed)` and derived substreams if parallel modules.

## Timing
- Synthetic activity calendar: `2024-01-01` through `2025-12-31` (24 months).
- Generate leads between Jan 2024 and Mar 2025 inclusive, with variable seasonal volume and channel mix, so every acquisition (within 30 days) has full 90+180-day follow-up by end of 2025; if end dates change, derive eligibility dynamically rather than relying on this assumption.
- Transaction activity extends through Dec 2025; visits prior to leads are synthetic pre-lead features.
- Explicit 180-day outcome measured **from lead date** for RCT and **from 90-day acquisition checkpoint** for ML. These are different, labeled horizons and are never conflated.

## Realism with reproducibility
Market effects, monthly seasonality, channels, engagement, and financial values vary with noise. Some channels convert more but cost more, some offer variants may help conversions while costing more; make heterogeneity plausible. There should be a near-zero or negative net treatment effect in at least one deterministic slice to avoid a sales-pitch dataset. No unrealistic perfect labels.

### Conversion generation
1. Draw market/channel/segment assignment and pre-lead variables independently of random treatment assignment.
2. Within each `market × channel × lead_month` stratum assign treatment/control using seeded permutation or random Bernoulli and test balance. Choose assignment before outcome simulation.
3. Draw conversion from a bounded logistic probability function that depends on pre-lead engagement, market, channel, month seasonality and treatment offer effect. Keep probabilities e.g. 0.02–0.45 and avoid near-perfect prediction.
4. Convert within 0–30 days of lead for converters. Generate one customer per converted lead.
5. Conditional on conversion, generate purchases over time with stochastic retention, frequency and transaction values, positive variable costs and servicing costs; customers can churn and have no later transactions.
6. Incentive payouts occur only for some converters in treatment arm; payout amount may vary by variant/market (USD-converted). Never make payout amount depend on realized future outcomes in a way that creates a hidden observed-data leak.

### Campaign budgets
Generate planned vs actual monthly spending in USD for each market/channel/month; `actual` constrained nonnegative, planned may be zero but define safe utilization. Set coherent links: more spend tends to associate with more lead volume without claiming causality. Add a few plausible over/underutilization cases, no impossible negative spend. Default optimization baseline allocations draw from observed recent 3-month spend normalized to a user budget; if none, equal split.

### Transaction economics
A transaction has gross revenue, direct variable cost and optional fixed servicing cost; `contribution = gross - costs`. The same costs must not be deducted twice in LTV, ROI or optimizer. Campaign spend and welcome-offer payouts remain separate and are not in transaction contribution.

### Metadata
Save `manifest.json` with generator version, seed, generation start/end, lead count, table row counts, fx assumptions, approximate spend totals and SHA256 hashes of parameter files. README labels values as synthetic and not Amex data.

### Important controls
- Never emit national IDs, names, postal addresses, account numbers, medical or protected characteristics.
- Keep real-world country/currency codes but disclose exchange rates are fixed synthetic assumptions.
- Do not expose internal latent truth or simulator coefficient arrays as features for modeling, evaluation or optimizer inputs. This ensures honest assessment of model behavior.
- Avoid datasets so clean that cleaning work is meaningless: inject a *separate optional corruption fixture* for tests, while the generator's canonical dataset remains valid. Do not corrupt production demonstration datasets without flags.
