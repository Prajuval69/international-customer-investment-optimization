# 00 — Product Brief and User Stories

## Problem
International finance/marketing stakeholders must understand how much acquisition investment is consumed, whether randomized welcome offers improve net cohort value, which markets/channels deliver attractive customer economics, and where an *assumed* future budget could be allocated. Build an educational simulation demonstrating credible analyst workflow rather than a promotional dashboard.

## User stories
- As a Finance Analyst, I can inspect acquisition counts, margin, CAC, investment utilization and ROI by month/market/channel, with clear denominators and reconciliation checks.
- As a Data Scientist, I can fit/test 90-day checkpoint models to estimate subsequent 180-day customer contribution and compare to a cohort-average baseline without future-data leakage.
- As a Marketing Analyst, I can evaluate randomized welcome-offer assignment with an intention-to-treat analysis that keeps all assigned leads (including zeros for no conversion), confidence intervals, costs and uncertainty.
- As a Planner, I can allocate a fixed hypothetical budget subject to channel/market bounds, view original versus optimized expected net returns, and explore uncertainty in response assumptions.
- As an Executive, I can read fast explanations of KPIs, key drivers and caveats, filter a market/date/channel and export reproducible evidence.

## MVP acceptance
Six Streamlit pages; five markets; deterministic synthetic event tables; validated DuckDB mart; at least 10 meaningful charts/tables overall; one ML customer-value model with baseline, one valid RCT estimator, one correctly constrained nonlinear optimizer; CLI and automated tests; reproducible export package.

## Scope guards
In-scope: synthetic international financial-services-style acquisition economics, attribution assumptions, short-horizon LTV modeling, experiments, investment scenarios, KPI scorecards, CSV/XLSX reporting.

Out-of-scope: real Amex data, credit risk scoring, underwriting decisions, regulated advice, PII, real exchange rate quotes, actual future revenue claims, real causal effects from observational spend trends, production authentication, real-time integrations, LLM assistants, mandatory GCP/Hive/PySpark/Power BI, enterprise microservices.

## Key decisions
- USD is the common reporting unit. Currency FX rates are simulated constant *illustrative assumptions*, not current market rates.
- Each financial measure records its cost components and reporting horizon.
- User-visible outcomes must be computed from the pipeline, not hardcoded samples.
- A marketing attribution model is not a causal experimentation result.
- Every modeled/estimated/simulated number should be clearly differentiated from historical synthetic actuals.
