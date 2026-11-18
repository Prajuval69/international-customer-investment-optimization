# 13 — Resume, GitHub and Interview Usage

## Responsible positioning
This project is independent synthetic-data work tailored to the kinds of analytical responsibilities in the American Express job description. Never suggest it was made for, reviewed by, or deployed at American Express. Distinguish code that has been **implemented and verified** from the planned spec in this ZIP.

## Possible resume project title
**International Customer Acquisition & Marketing Investment Optimization** | Python, SQL, DuckDB, scikit-learn, SciPy, Streamlit

## Resume bullet drafts — use ONLY after implementation and verification
- Engineered a reproducible Python–DuckDB analytics pipeline for simulated acquisition, incentive, and transaction data across five markets, calculating market-level CAC, 180-day cohort profitability, marketing ROI and budget utilization.
- Developed a time-validated customer-value prediction model using first-90-day behavior to predict subsequent 180-day contribution margin; benchmarked against a cohort baseline and reported held-out error metrics.
- Evaluated randomized welcome-offer assignments using lead-level intention-to-treat estimates and confidence intervals, then built a constrained SciPy budget-allocation simulator with diminishing-return assumptions and scenario sensitivity analysis.

Update these bullets to match whatever was **actually** built; include verified sample size, test count, quantitative error or objective improvement only from measured outputs. The optimizer improvement is simulated projected profit **under assumptions**, not observed realized uplift. Do not call the model full lifetime LTV.

## Interview practice questions
1. Why is 90-day activity usable for predicting next-180-day customer value, but not for deciding which lead to acquire at the time of acquisition?
2. How do you prevent campaign spend duplication when joining budgets with many customer transactions?
3. Why must the primary A/B outcome include non-converting assigned leads, and why is per-converter analysis biased?
4. How do you distinguish a randomized welcome-offer causal effect from observational market/channel spend ROI?
5. What happens to optimizer constraints and marginal returns when budget grows or upper bounds bind?
6. How do you calculate CAC, cohort ROI, and investment utilization, and handle zero denominators?
7. How do you form chronological train/validation/test splits, choose a baseline and interpret predictive bias?
8. If a market has strong conversion but weak contribution margin, would you increase budget? Under what assumptions?

## GitHub checklist
Readable README with screenshots from a **real executed dashboard** (if captured), quickstart that works, explicit synthetic-data disclaimer, architecture diagram, model/experiment methodology, assumption tables, example output, automated tests and truthful results. Include no generated secrets, proprietary materials or personally identifiable data.
