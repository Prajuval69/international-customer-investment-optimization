# Codex Build Pack — International Customer Acquisition & Marketing Investment Optimization

**Target:** American Express Analyst – Data Science (Job ID 26015352) — independent educational portfolio project, **not** an American Express product, dataset, or affiliation.

This ZIP is a comprehensive **specification and master prompt** for Codex. It is **not** an already implemented application. Codex should create the app in a new repository by following the instructions inside.

## What Codex must deliver
A working, fully offline Python/SQL/ML application that (1) creates deterministic synthetic data for five international markets, (2) computes and visualizes customer acquisition, profitability, marketing ROI and LTV, (3) evaluates randomized welcome-offer experiments, (4) optimizes a constrained marketing budget using clearly labeled scenario assumptions, and (5) exposes a polished Streamlit dashboard with exports, tests and reproducible setup instructions.

No credentials, paid API, cloud project, Docker installation, real customer data, or external database service should be required. PySpark, Hive, and GCP are deliberately **not** claimed unless genuinely implemented later.

## Start in Codex
1. Extract the ZIP into a new empty repository or provide it as the Codex workspace.
2. Open `MASTER_CODEX_PROMPT.md` and give Codex the prompt verbatim as its task.
3. Allow Codex to create, install, execute, test and revise files in that workspace.
4. When Codex finishes, run the verification commands in `docs/11_ACCEPTANCE_TESTS.md` and inspect dashboard screenshots before describing the project as complete.

The instructions are broken down by topic to keep the autonomous build manageable:

| File | Purpose |
| --- | --- |
| `MASTER_CODEX_PROMPT.md` | Paste-this master execution instruction |
| `docs/00_PRODUCT_BRIEF.md` | Scope, user stories, MVP, constraints |
| `docs/01_ARCHITECTURE.md` | Tech stack, architecture, repository structure |
| `docs/02_DATA_CONTRACTS.md` | Source tables, types, keys, warehouse and KPI grain |
| `docs/03_SYNTHETIC_GENERATOR.md` | Reproducible, realistic generator, temporal validity |
| `docs/04_ETL_AND_SQL.md` | Data validation, DuckDB views and warehouse metrics |
| `docs/05_LTV_AND_ML.md` | LTV methodology, model training, leakage defenses |
| `docs/06_EXPERIMENTATION.md` | Welcome-offer randomized trial and confidence intervals |
| `docs/07_ECONOMICS_AND_OPTIMIZATION.md` | ROI accounting, constrained spend optimization |
| `docs/08_DASHBOARD_AND_UX.md` | Complete Streamlit page and visualization spec |
| `docs/09_CLI_REPORTING.md` | Commands, exports, documentation and workflow |
| `docs/10_ENGINEERING_RULES.md` | Code quality, dependency rules and error handling |
| `docs/11_ACCEPTANCE_TESTS.md` | Verification, tests and definition of done |
| `docs/12_IMPLEMENTATION_SEQUENCE.md` | Ordered autonomous work plan and stop conditions |
| `docs/13_INTERVIEW_AND_RESUME.md` | Ethical resume statements and interview prep |
| `docs/14_METRIC_GLOSSARY.md` | Unambiguous KPI definitions and display labels |

## Strict truthfulness
- All customer, prospect, transaction and market results are synthetic; display that in the UI and reports.
- Do not treat observational differences across channels as causal uplift.
- Do not train on generated latent variables or use future outcomes in features.
- **LTV 90-day checkpoint predictions cannot be used for decisions made at prospect acquisition time**; optimization must instead use lead-time cohort economics / explicitly labeled assumptions.
- Optimizer results are scenarios, not observed ROI or guaranteed business outcomes.
- Never claim actual Amex client impact or deployment.

If multiple implementations are viable, favor reliability, comprehensibility, fast execution and testable mathematics over extra infrastructure.
