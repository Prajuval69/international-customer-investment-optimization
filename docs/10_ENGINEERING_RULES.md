# 10 — Engineering Quality, Local-First Constraints and Safety

## Requirements
- Python 3.11 or newer; `pyproject.toml` installable `pip install -e '.[dev]'`. Dependencies: numpy, pandas, pyarrow, duckdb, scipy, scikit-learn, statsmodels, plotly, streamlit, joblib, openpyxl, pyyaml, pytest, ruff. Only add packages needed.
- No cloud/API credentials, network requests, database servers, downloaded ML datasets, Docker requirement, GPU or LLM service.
- Keep synthetic default small enough for modest laptop: 30k leads, model training CPU-friendly; allow `--leads 1500` smoke demo.
- Make the CLI and tests work cross-platform (Windows PowerShell and macOS/Linux), no shell-specific scripts required for running.
- Strong typing when helpful, unit-test pure business math, isolate I/O and Streamlit, explicit config validation, human-friendly exceptions and logging.
- SQL parameterization for user filters and separate financial metric functions with docstrings/formulas.
- Never use arbitrary `eval`, pickle untrusted external files, execute shell via dashboard, or expose unneeded PII.

## Meaning and model governance
- Indicate generated values, uncertainty, segment sample sizes and analytical limitations.
- Missing FX or cost fields should fail loudly; do not silently substitute zeros.
- Negative/zero denominators: return `None`/null + UI N/A (not infinity).
- All spending/incentives in same currency and horizon before aggregation; fixed rates are assumptions.
- Avoid unrelated buzzword claims (Hive/GCP/PySpark/SHAP/Power BI) unless actually implemented; DuckDB SQL and Streamlit are enough.
- Note statistical tests on simulated randomly assigned leads can demonstrate inference mechanics; effect sizes are simulator-dependent and do not generalize to real campaigns.

## CI and testing
`ruff check .` and `pytest -q` must succeed. Include optional GitHub Actions on Python 3.11 for install + tests + synthetic smoke; no tokens/secrets. Deterministic seeds in tests, quick run, no tests requiring outside internet after dependencies installed.

## Integration conventions
- Idempotent `demo`; no multiple mutated source artifacts after identical seed runs.
- All report file names stable.
- Any project status claim in final Codex response must be based on executed/observed commands, not aspiration.
- Document remaining limitations instead of masking errors.
