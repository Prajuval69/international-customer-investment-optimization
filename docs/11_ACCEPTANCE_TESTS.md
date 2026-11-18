# 11 — Acceptance Criteria and Test Matrix

## User-level commands
From root after successful installation:
```
python -m pip install -e '.[dev]'
python -m investopt demo --seed 42
python -m investopt smoke
python -m investopt optimize --budget 1000000
pytest -q
ruff check .
streamlit run app/Home.py --server.headless true
```
For the dashboard test, terminate headless server after verifying it starts and exhibits no import errors. Optional browser screenshot/e2e if available. If optimization budget $1M is outside configured feasible range, change defaults to make this example feasible or print documented allowed interval; ensure README sample actually works.

## Must-pass automated tests (>=30 meaningful checks across categories)

**Generator (6+)**
1. Fixed seed produces same manifest/table values; different seed changes values.
2. All IDs unique, rows stable, currencies/market keys valid.
3. One customer per converted lead, no customer for nonconverters.
4. Transaction dates >= acquisition; cost components reconcile.
5. Treatment/control assignment both present in each sufficiently large stratum and no assignment from outcome.
6. Zero/negative/invalid spend rejected; alternate seed/small volume succeeds.

**Warehouse/metrics (6+)**
7. Sum campaign spend by campaign equals raw spend, invariant to transaction joins.
8. Exactly one experiment outcome per randomized lead.
9. Zero conversion and zero cost denominators produce N/A rather than inf.
10. Cohort 180-day maturity and exact date boundaries tested.
11. `profit = contribution - campaign_spend - incentives`, ROI match toy calculation.
12. Aggregation by market/channel reconciles to overall.

**Machine learning (5+)**
13. Features have no future activity; labels strictly after day-90 checkpoint.
14. No incomplete label window; no duplicate customers.
15. Chronological train/validation/test split, disjoint customer membership.
16. Baseline fitted on training only; same seed produces deterministic outputs.
17. Held-out predictions finite, shape correct; metrics and version saved.

**Experiment (6+)**
18. RCT includes all assigned leads and zero for nonconverters.
19. Incentive costs applied only to treatment payouts exactly once.
20. ITT arithmetic matches hand-computed toy example.
21. 95% interval returns finite bounds and valid ordering.
22. Statistical N uses leads not transaction rows; duplicate transaction cannot affect N.
23. Low sample size/one-arm stratum produces clear warnings or excluded-stratum diagnostics.

**Optimizer (6+)**
24. Diminishing returns and nonnegative response at zero spend.
25. Known profit objective matches component breakdown.
26. Spend exactly conserved within tolerance.
27. Every allocation obeys min/max, nonnegative.
28. Infeasible budget rejected (too low and too high).
29. Optimized objective >= feasible baseline to within tolerance; repeat deterministic.

**Dashboard/report (3+)**
30. Report export contains real pipeline outputs, synthetic label and known column schema.
31. Filters drive changes in query output, not static fixtures.
32. Smoke checks actual artifact existence, row counts and nonempty models/reports; missing files fail with guidance.

Add more tests for edge conditions when practical; do not write tests that just assert `True`.

## Golden toy math fixture
A mature cohort has 10 leads, 2 conversions, campaign spend $100, contribution $180, welcome payout $20. Then CAC=`(100+20)/2=$60`; net after acquisition costs=`180-100-20=$60`; ROI=`60/120=0.5` (50%); conversion rate=20%; if planned spend $80, utilization=125%. Add fixture exercising these exact values. Prevent misuse: experimental ITT excludes spend unless separately attributed.

## Completion review
- [ ] Fresh environment install and `demo` succeed (record actual run).
- [ ] `smoke`, `pytest -q`, `ruff check .` succeed (record actual results).
- [ ] Dashboard all pages render with nonempty calculations and disclaimers.
- [ ] LTV test metrics and holdout periods visible, honest versus baseline.
- [ ] RCT uses lead-level ITT and includes CIs and caveats.
- [ ] Optimizer feasible and clearly scenario-based; sensitivity functions.
- [ ] Reports/CSV/XLSX reconcile to warehouse.
- [ ] No fake screenshots, impact numbers, or unverified achievements.
- [ ] README quickstart instructions work as written.
