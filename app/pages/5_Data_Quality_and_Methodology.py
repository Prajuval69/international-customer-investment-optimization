import pandas as pd
import streamlit as st

from app.components import P, data, header, read_json
from investopt.config import configuration
from investopt.optimizer import assumptions
from investopt.validation import REQUIRED

manifest = header(
    "Data quality & methodology",
    "Inspect source contracts, reconciliation, reproducibility and analytical boundaries.",
)
dq = read_json(P.artifacts / "data_quality.json")
checks = pd.DataFrame(dq["checks"])
cols = st.columns(3)
cols[0].metric("Source contract checks", len(checks))
cols[1].metric("Failed checks", int((~checks.passed).sum()))
cols[2].metric("Synthetic seed", manifest["seed"])
st.dataframe(
    pd.DataFrame(list(dq["row_counts"].items()), columns=["table", "rows"]), hide_index=True
)
st.dataframe(checks, hide_index=True)
st.subheader("Source missingness")
st.dataframe(pd.DataFrame(dq["missingness"]).fillna("—"))
st.caption(
    "Lead customer_id and conversion_date are intentionally null for nonconverters. Other required fields are checked as nonnull."
)
st.subheader("Reconciliation")
st.json(read_json(P.artifacts / "reconciliation.json"))
st.subheader("Fixed illustrative exchange rates")
st.dataframe(data("markets"), hide_index=True)
st.caption(
    "Fictional fixed conversion assumptions, not current FX quotes. USD values are used for all aggregation."
)
with st.expander("Data dictionary & provenance", expanded=False):
    st.json(REQUIRED)
    st.json(manifest)
    st.json(read_json(P.artifacts / "demo_manifest.json"))
st.subheader("Accounting & aligned follow-up")
st.write(
    "Contribution = gross transaction revenue − direct variable costs − servicing costs. Campaign spend and paid incentives are separate. CAC = (campaign spend + payouts)/acquisitions. Cohort ROI = (contribution − campaign spend − payouts)/(campaign spend + payouts). Undefined denominators are N/A."
)
st.write(
    "Customer cohort contribution uses acquisition days 0–180 inclusive. Lead experiments use lead days 0–180 inclusive. Campaign-month maturity conservatively requires month end + 30 conversion days + 180 outcome days. Segment spend is allocated in proportion to eligible lead counts, once per campaign."
)
st.subheader("Temporal modeling & randomized inference")
st.write(
    "Model features use transactions on/before acquisition day 90. Discounted target uses days 91–270. Cohort months are split chronologically ~60/20/20. Hyperparameters use validation MAE; final refit uses train + validation, while the baseline remains the original training median. Test is never used for selection."
)
st.write(
    "Randomization is balanced within market × channel × lead month before conversion. ITT retains all mature eligible leads including zeros. Welch intervals are unadjusted; Newcombe intervals cross-check conversion differences. Single-arm strata and low samples are flagged. Exploratory subgroup comparisons have no multiplicity correction."
)
st.subheader("Scenario assumptions")
st.dataframe(assumptions(P.root), hide_index=True)
cfg, hashes = configuration(P.root)
with st.expander("Configuration and parameter hashes"):
    st.json({"parameters": cfg, "sha256": hashes})
st.subheader("Limitations & local documentation")
st.write(
    "Independent synthetic demonstration; no real customer, Amex, underwriting or credit-risk data. Optimizer inputs are hypothetical assumptions; simulated results do not imply real causal impact. Model uncertainty is approximate and short-horizon. No production identity/access control or live data integration is implemented."
)
st.write(
    "The generator derives a safe lead cutoff from the observation end: March 6, 2025 for the default calendar. This corrects the specification's overly optimistic March 31 maturity assumption."
)
for label, file in [
    ("README", P.root / "README.md"),
    ("Methodology", P.root / "docs/METHODOLOGY.md"),
]:
    if file.exists():
        st.download_button(
            f"Download {label}", file.read_bytes(), file_name=file.name, mime="text/markdown"
        )
