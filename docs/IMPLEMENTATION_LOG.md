# Execution plan and decisions

1. Read the master prompt and all original specifications (completed).
2. Implement and verify deterministic generator and strict validation.
3. Implement SQL marts, accounting and cohort reconciliation.
4. Train temporal customer-value model with baseline and validation selection.
5. Evaluate randomized lead-level offers with uncertainty and diagnostics.
6. Implement constrained scenario optimization and sensitivity.
7. Build six Streamlit pages from warehouse and generated artifacts.
8. Export reports, finish documentation, execute acceptance commands and inspect UI.

The user explicitly requires Streamlit and a local offline Python application;
these requirements govern the rendering/runtime rather than Data's default HTML app.
Use the Data skill's analytical quality guidance, filtered exports, and visual QA.
Source authority is the supplied specifications and generated synthetic event tables.
No external sources, real business claims, paid services or runtime network are needed.

SQL scripts are packaged under investopt/sql so editable and wheel installs share them.
Original numbered specification files are preserved in docs/spec.

## Completed execution

Phases 0–8 completed in order. The default 30,000-lead demo ran twice with identical
source manifests and model/baseline metrics. Calendar eligibility derives March 6,
2025 rather than assuming March 31 allows complete 300-day follow-up. All source
specifications remain preserved. SQL aggregation and financial invariants, leakage
controls, lead-level RCT and optimizer constraints were exercised by 65 passing tests.
Ruff, smoke, pip consistency, CLI optimization and Streamlit startup succeeded.
Six-page AppTest and actual browser review were performed; local screenshots are
real captures. Command logs and limitations are in docs/VERIFICATION.md and
reports/verification. No remote deployment or CI execution is claimed.
