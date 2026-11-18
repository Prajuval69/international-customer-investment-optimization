# Local verification record

Independent synthetic portfolio application; no actual customer or business impact.

## Executed checks

Environment: Windows, Python 3.12.4, project-local `.venv`.

- Editable development installation succeeded, exit 0.
- Default `python -m investopt demo --seed 42` succeeded, exit 0: generation,
  validation, SQL build, training, experiment, optimization, reporting and smoke.
- Default generated rows: 5 markets, 300 campaigns, 30,000 leads, 6,087 customers,
  146,486 transactions and 2,477 payouts.
- Most recent completed suite: 65 tests passed. Final command logs after all
  revisions are retained in `reports/verification/`.
- Streamlit started in headless mode on loopback port 8501. All six pages rendered
  with AppTest. Market filters, empty selections, infeasible budgets and missing-data
  behavior were exercised. Real browser review complements automated checks.

## Measured results, seed 42

Held-out test: 1,226 customers, acquisition cohorts January–April 2025. Model MAE
$79.9054, RMSE $140.8695; training-median baseline MAE $104.6805, RMSE $206.8703.
Task: next 180-day discounted contribution from acquisition day-90 checkpoint.

RCT: treatment 15,008, control 14,992. Net ITT -$4.8701 per assigned lead; 95% Welch
CI [-$6.9477, -$2.7924], p approximately 0.00000436. Conversion lift +1.7184 pp;
payout costs outweighed additional lead margin in this synthetic experiment.

Default $1M campaign-budget scenario: feasible recent-spend baseline projected profit
$1,842,371.29, optimized $1,911,035.43, additional expected incentives $319,114.46.
These are hypothetical planning results, not observed marketing impact.

## Scope and limitations

Verified locally on Windows with CPU execution. A Python 3.11 Linux GitHub Actions
workflow is supplied; remote CI execution has not been observed. No public deployment,
live data/FX, production authentication or actual marketing impact is claimed.
Results depend on simulator/assumptions and seed; exact artifacts record provenance.
Operational timestamps change intentionally on rerun. Real screenshots, where captured,
are stored under `reports/screenshots/`; no screenshots are synthesized.

## Final acceptance results

Final recorded commands on October 25, 2026 all succeeded:

| Command | Observed result |
|---|---|
| `python -m pip install -e '.[dev]'` | Installed successfully, exit 0 |
| `python -m investopt demo --seed 42` | Full pipeline plus smoke, exit 0 |
| `python -m investopt smoke` | Hashes, counts, spend and saved predictions pass, exit 0 |
| `python -m investopt optimize --budget 1000000` | Feasible constrained solution, exit 0 |
| `pytest -q` | **65 passed in 14.72 seconds**, exit 0, no warnings |
| `ruff check .` | All checks passed, exit 0 |
| `python -m pip check` | No broken requirements, exit 0 |
| Streamlit headless startup | Loopback URL active; health endpoint HTTP 200, body `ok` |
| Default rerun reproducibility | Source manifests, model metrics and baseline identical |

Raw outputs and exit codes: `reports/verification/demo.txt`, `pytest.txt`, `ruff.txt`,
`smoke.txt`, `optimize.txt`, `reproducibility.json` and `streamlit_health.json`.
Browser review used the actual local app, including narrow-screen cards and charts.
The local server remains available at http://127.0.0.1:8501 while its process runs.
On this mapped drive, restarting Streamlit was needed to refresh imported UI modules;
restart the server after editing shared Python code if a page still shows old content.

