"""Validated SQL ETL with transactional replacement and grain checks."""

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from investopt.config import configuration, write_json
from investopt.generator import TABLES
from investopt.paths import paths
from investopt.validation import validate


def connect(root=None, read_only=True):
    p = paths(root)
    if read_only and not p.db.exists():
        raise ValueError("Warehouse missing. Run: python -m investopt demo --seed 42")
    return duckdb.connect(str(p.db), read_only=read_only)


def reconcile(con):
    source, mart = con.execute(
        "SELECT (SELECT sum(actual_spend_usd) FROM campaign_budget), (SELECT sum(actual_spend_usd) FROM mart_campaign_month)"
    ).fetchone()
    lead_n, exp_n, distinct_n = con.execute(
        "SELECT (SELECT count(*) FROM leads),count(*),count(DISTINCT lead_id) FROM mart_experiment_lead_outcomes"
    ).fetchone()
    result = {
        "spend_source_usd": source,
        "spend_mart_usd": mart,
        "lead_count": lead_n,
        "experiment_count": exp_n,
        "passed": bool(np.isclose(source, mart) and lead_n == exp_n == distinct_n),
    }
    if not result["passed"]:
        raise ValueError("Warehouse grain reconciliation failed")
    return result


def build(root=None):
    p = paths(root).prepare()
    validate(p.root)
    cfg, _ = configuration(p.root)
    manifest = json.loads((p.raw / "manifest.json").read_text())
    with connect(p.root, read_only=False) as con:
        con.begin()
        try:
            for name in TABLES:
                frame = pd.read_parquet(p.raw / f"{name}.parquet")
                con.register("input_frame", frame)
                con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM input_frame')
                con.unregister("input_frame")
            meta = pd.DataFrame(
                {
                    "observation_end": [pd.Timestamp(manifest["observation_end"])],
                    "annual_discount_rate": [cfg["scenario"]["annual_discount_rate"]],
                }
            )
            con.register("meta_frame", meta)
            con.execute("CREATE OR REPLACE TABLE metadata AS SELECT * FROM meta_frame")
            for sql in sorted((Path(__file__).parent / "sql").glob("*.sql")):
                con.execute(sql.read_text())
            result = reconcile(con)
            con.commit()
        except Exception:
            con.rollback()
            raise
    write_json(p.artifacts / "reconciliation.json", result)
    return result
