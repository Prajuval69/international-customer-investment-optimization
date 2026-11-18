# 12 — Autonomous Codex Implementation Plan

**Treat this as an execution checklist; continue to implementation and verification in the same Codex task, not a request for additional approvals.**

## Phase 0 — Understand and scaffold
Read all specifications. Create package, `pyproject.toml`, settings loader, docs directory, baseline tests, CLI. Decide precise schema and record it. Execute imports.

## Phase 1 — Data generator and schema
Generate five-market table set and manifest from one seed. Add contract validation including conversion/customer matching, contribution reconciliation, dates, and known treatments. Use tiny tests then default-size generation.

## Phase 2 — DuckDB warehouse and business KPIs
Implement SQL scripts and materialize granular and aggregate marts. Verify no double-counted spend, correct cohort time windows, and golden economics fixture. Wire `generate`, `validate`, `build`.

## Phase 3 — ML customer value
Implement day-90-only feature extraction and next-180-day value label, time-ordered split, preprocessing, baseline, trained model, evaluation, artifacts. Verify no leakage; supply diagnostics. Wire `train`.

## Phase 4 — Randomized welcome-offer experiment
Create lead-level ITT estimator, conversion effect, cost difference, intervals, subgroup diagnostics and outputs. Cross-check hand-calculated synthetic toy cases. Wire `experiment`.

## Phase 5 — Financial planning and optimizer
Build scenario config (with distinct assumed spend curves), max/min validations, feasible baseline, SciPy optimization and 3-scenario sensitivity. Verify economics do not reuse day-90 LTV at lead-time. Wire `optimize`.

## Phase 6 — Streamlit dashboard
Create overview + five pages. All cards/charts from live generated outputs; filters working, no fake values. Include synthetic banner and scenario disclaimers. Handle no data gracefully.

## Phase 7 — Exports, reports, documentation
Build Markdown, CSV and XLSX reporting and methodology/README. Generate sample report figures and screenshots if browser tooling allows. Supply architecture and assumptions.

## Phase 8 — Verification and repair
Execute fresh-run commands from `docs/11_ACCEPTANCE_TESTS.md`, fix issues, confirm tests and format. Ensure `demo` is idempotent for same seed. Document actual results and known limitations. A README alone is not completion.

## Priorities when constrained
1. Correct data + SQL financial reconciliation
2. Correct randomized experiment / causal boundaries
3. ML no leakage + test comparison
4. Scenario optimization + constraints
5. Functional six-page dashboard
6. Tests + documentation/exports
7. Nice-to-have screenshot automation and advanced visuals

Do not drop a required item silently. If tool execution is unavailable, write complete code and honestly mark verification blockers.
