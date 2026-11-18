"""Orchestration and strict artifact smoke checks."""

import hashlib
import importlib
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from investopt.config import write_json
from investopt.experiment import experiment
from investopt.generator import TABLES, generate
from investopt.ltv import FEATURES, train
from investopt.optimizer import optimize
from investopt.paths import paths
from investopt.reporting import report
from investopt.validation import validate
from investopt.warehouse import build, connect, reconcile


def fingerprint(p):
    return hashlib.sha256((p.raw / "manifest.json").read_bytes()).hexdigest()


def demo(seed=42, leads=30000, root=None):
    p = paths(root).prepare()
    for name, action in [
        ("generate", lambda: generate(seed, leads, p.root)),
        ("validate", lambda: validate(p.root)),
        ("build", lambda: build(p.root)),
        ("train", lambda: train(seed, p.root)),
        ("experiment", lambda: experiment(seed, p.root)),
        ("optimize", lambda: optimize(1000000, p.root)),
        ("report", lambda: report(p.root)),
    ]:
        print(f"Running {name} ...", flush=True)
        action()
    manifest = json.loads((p.raw / "manifest.json").read_text())
    write_json(
        p.artifacts / "demo_manifest.json",
        {
            "synthetic": True,
            "seed": seed,
            "data_manifest_sha256": fingerprint(p),
            "model_version": "1.0.0",
            "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "row_counts": manifest["row_counts"],
            "parameter_hashes": manifest["parameter_hashes"],
        },
    )
    return smoke(p.root)


def smoke(root=None):
    p = paths(root)
    required = [p.db, p.raw / "manifest.json"] + [p.raw / f"{n}.parquet" for n in TABLES]
    required += [
        p.artifacts / name
        for name in [
            "ltv_model.joblib",
            "model_metrics.json",
            "feature_schema.json",
            "holdout_predictions.parquet",
            "experiment_results.json",
            "optimizer_results.json",
            "data_quality.json",
            "demo_manifest.json",
        ]
    ]
    required += [
        p.reports / name
        for name in [
            "executive_summary.md",
            "kpi_scorecard.csv",
            "experiment_summary.csv",
            "optimizer_allocation.csv",
            "model_metrics.json",
            "data_quality.md",
            "analytics_report.xlsx",
        ]
    ]
    missing = [str(file) for file in required if not file.exists() or file.stat().st_size == 0]
    if missing:
        raise ValueError(
            "Missing artifacts: " + ", ".join(missing) + ". Run: python -m investopt demo --seed 42"
        )
    run = json.loads((p.artifacts / "demo_manifest.json").read_text())
    manifest = json.loads((p.raw / "manifest.json").read_text())
    if run["data_manifest_sha256"] != fingerprint(p):
        raise ValueError("Pipeline artifacts are stale; rerun demo")
    for name in TABLES:
        if (
            hashlib.sha256((p.raw / f"{name}.parquet").read_bytes()).hexdigest()
            != manifest["table_hashes"][name]
        ):
            raise ValueError(f"Raw {name} fingerprint changed; rerun demo")
    validate(p.root)
    for module in ["streamlit", "plotly", "openpyxl"]:
        importlib.import_module(module)
    with connect(p.root) as con:
        result = reconcile(con)
        for name, n in manifest["row_counts"].items():
            if con.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0] != n:
                raise ValueError(f"Source/warehouse row mismatch: {name}")
        model = joblib.load(p.artifacts / "ltv_model.joblib")  # local, generated artifact only
        held = pd.read_parquet(p.artifacts / "holdout_predictions.parquet").head(5)
        features = (
            con.execute("SELECT * FROM mart_customer_checkpoint_90d")
            .df()
            .set_index("customer_id")
            .loc[held.customer_id]
        )
        if not np.allclose(model.predict(features[FEATURES]), held.prediction_usd):
            raise ValueError("Saved model does not reproduce held-out predictions")
    result.update(
        {"synthetic": True, "row_counts": manifest["row_counts"], "reports": str(p.reports)}
    )
    return result
