# 02 — Data Contracts, Grain, Keys and Tables

## Canonical conventions
- All IDs unique and stable for fixed seed (e.g. `L0000001`, `C0000001`).
- Dates `date` or UTC timestamp. Monthly reporting by calendar month from `lead_date`/`txn_date` with clear attribution.
- Monetary unit suffix `_usd` is the only monetary source for aggregation; local values require market FX conversion from `market_fx` metadata. Do not mix currencies.
- `market` in `{IN,GB,CA,AU,SG}`; `channel` in `{Search,Social,Referral,Partnership}` (optimizer can use 2+ active channels). Markets: India, United Kingdom, Canada, Australia, Singapore.
- Channel allocation metrics operate at `market × channel × month` grain; do not multiply a campaign's total spend by each lead when joining.
- Experimental unit is one **lead**, not one customer or transaction. Randomization stratified by market × channel × lead month with a 50/50 assignment and 1 row per lead.
- Use synthetic attributes only: engagement, visit count, broad interest/behavior segment, lead source, not protected demographic attributes, PAN/card numbers, names, emails or addresses.

## Raw tables (minimum)

### `markets` (5 rows)
`market` (PK), `name`, `local_currency` (ISO 4217), `usd_per_local_unit` (positive, illustrative fixed FX), `fx_assumption_date` (text: 'synthetic baseline'). Example currencies INR, GBP, CAD, AUD, SGD. Document exchange rates as fictional assumptions, no live rates.

### `campaign_budget` (1 row per market/channel/month)
`campaign_id` (PK), `market`, `channel`, `month_start`, `planned_spend_usd` >= 0, `actual_spend_usd` >= 0, `campaign_status`. `utilization=actual/planned` when planned>0. Prohibit duplicate `(market,channel,month_start)`.

### `leads` (1 row per eligible prospect)
`lead_id` (PK), `lead_date`, `market`, `channel`, `campaign_id` (FK to market/channel/month), `synthetic_segment`, `site_visits_pre_lead`, `engagement_score_pre_lead`, `offer_arm` (`treatment`/`control`), `offer_variant` (treatment offer name, control `none`), `converted` (0/1), `customer_id` (nullable, unique when non-null), `conversion_date` (nullable). Conversions occur within 30 days of lead. Store random assignment independent of outcomes, immutable.

### `customers` (converted leads only)
`customer_id` (PK), `lead_id` (unique FK), `acquisition_date`, `market`, `channel`, `synthetic_segment`, `offer_arm`. Verify number of customers equals converted leads and acquisition_date >= lead_date.

### `transactions` (multiple rows per customer)
`transaction_id` (PK), `customer_id` (FK), `txn_date` >= acquisition date, `gross_revenue_usd` >= 0, `direct_variable_cost_usd` >= 0, `servicing_cost_usd` >= 0, `contribution_usd` = gross revenue - direct variable cost - servicing cost. Loss-making transactions allowed; label appropriately.

### `offer_payouts` (zero or one event for each converted treatment lead)
`payout_id` (PK), `lead_id` (unique FK), `payout_date` >= conversion date, `incentive_cost_usd` >= 0; no control payouts. Generate some converted treatment customers who do not redeem; do not invent payouts for nonconverters.

### `scenario_assumptions` (source YAML/CSV, not inferred causal facts)
`market`, `channel`, `a_max_incremental_acquisitions`, `saturation_scale_usd`, `assumed_net_contribution_per_acquisition_usd`, `assumed_incentive_per_acquisition_usd`, `min_spend_usd`, `max_spend_usd`, optional `risk_multiplier`.

## Derived marts
- `mart_campaign_month`: campaign grain with lead_count, converted_count, assigned_treatment_count, assigned_control_count, total_margin_usd (attributed according to documented cohort windows), payout_cost_usd, actual_spend_usd and utilization.
- `mart_acquisition_cohort`: lead-month/market/channel/segment grain, mature 180-day cohort flags, lead counts, conversions, marketing spend allocated only once, 180d contribution and offer payouts.
- `mart_experiment_lead_outcomes`: exactly one row per **lead**: arm, market, channel, lead_month, converted, gross_contribution_180d_usd, incentive_cost_180d_usd, net_contribution_180d_usd = gross contribution - incentive cost. Use fixed follow-up after **lead date**; include zero for nonconverters.
- `mart_customer_checkpoint_90d`: exactly one row per customer with verified 90-day observation, numeric features observed up to end of checkpoint, `target_future_contribution_180d_usd` from checkpoint+1 to checkpoint+180d, maturity flag, market/channel/cohort. Checkpoint=acquisition_date + 90 days; transactions at dates <= checkpoint are features; subsequent dates <= checkpoint+180 are labels. No labels from incomplete follow-up.
- `mart_market_month`: grouped financial KPIs; do not report 180-day fully matured outcomes for incomplete cohorts.

## Referential and invariance checks
- Every lead's campaign market/channel/month equals its lead attributes.
- For each converted lead exactly one customer; for unconverted no customer.
- All transactions reference valid acquired customers; no transactions preceding acquisition.
- All payouts reference converted treatment leads only.
- `transactions.contribution_usd` reconciles exactly within small float tolerance.
- No duplicate keys; required fields nonnull; treatment randomization not outcome-conditioned.
- Cohort windows are fixed and explicitly labeled; incomplete cohorts excluded or shown separately.
- Sum of grouped spend across market/channel/month equals the campaign spend source, without transaction join multiplication.
- Document spend attribution: a cohort's campaign spend can be associated with lead-month cohorts, and 180d outcomes are earned later; don't imply accounting GAAP revenue recognition.
