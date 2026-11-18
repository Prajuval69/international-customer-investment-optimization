# 04 — ETL, Validation and SQL Analytics

## ETL sequence
1. Read Parquet raw tables; validate datatypes, business keys, referential integrity, dates, numeric ranges, arm assignment, campaign links and contribution reconciliation.
2. Materialize DuckDB normalized source tables, then mart tables/views from version-controlled `.sql` files.
3. Write a data quality report (`artifacts/data_quality.json` and human-readable `reports/data_quality.md`) with row counts, duplicates, missingness, invalid dates and reconciliation results.
4. Ensure idempotent reruns; `build` should replace target tables rather than append duplicates.

## SQL queries required
- Monthly actual/planned campaign utilization by market/channel; safe division.
- Leads, converts, conversion rate, acquisition count by same grain.
- Acquired cohort value after a *matured* 180-day window and payout cost by market/channel/segment, including zero-converting leads.
- Customer segment behavior (RFM features computed only as of 90-day checkpoint) and cohort averages.
- A lead-level experiment mart created with **preaggregated** 180d contributions per converted lead; avoid multiplying lead outcomes by transaction cardinality.
- A 90-day checkpoint ML mart with exactly one row/customer, a 180-day label from transactions after checkpoint, and historical features only at/before checkpoint.

## Reconciliation SQL tests
- SQL lead counts equal raw lead rows.
- Aggregate campaign spend never varies when more transaction rows are introduced.
- `count(distinct customer_id)` equals converted lead count.
- Sum of `gross_revenue - direct_cost - service_cost` equals sum of contribution.
- Experiment mart one row/lead and no missing net outcome: zeros for no conversion.
- All report output tables carry cohort age/maturity indicators so a 180d metric cannot silently include partially observed leads.

## Guidelines
Use parameters and query inputs safely, whitelist market/channel filters; no user-supplied SQL executed in dashboard. Prefer SQL for aggregations; Pandas only where statistical or modeling calculation benefits. Round only at presentation, never in core warehouse math. Store timestamp/date comparisons with explicit inclusive/exclusive boundaries and test boundary days. To avoid conflating calendar spend with historical outcome maturity, label ROI as acquisition-cohort ROI with 180-day follow-up, not periodic accounting profit.
