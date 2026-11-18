import numpy as np

from investopt.kpis import query, scorecard
from investopt.warehouse import connect, reconcile


def test_grain_reconciliation(warehouse):
    with connect(warehouse) as con:
        assert reconcile(con)["passed"]


def test_zero_nonconverters(warehouse):
    df = query("mart_experiment_lead_outcomes", warehouse)
    assert df.lead_id.is_unique
    assert df.loc[df.converted.eq(0), "net_contribution_180d_usd"].eq(0).all()


def test_filters_change_real_totals(warehouse):
    all_rows = query(root=warehouse)
    india = query(root=warehouse, markets=["IN"])
    assert 0 < india.lead_count.sum() < all_rows.lead_count.sum()
    assert query(root=warehouse, markets=[]).empty


def test_segment_spend_reconciles(warehouse):
    a = query(root=warehouse)
    b = query("mart_acquisition_cohort", warehouse)
    assert np.isclose(a.actual_spend_usd.sum(), b.allocated_spend_usd.sum())


def test_group_financial_reconciliation(warehouse):
    a = query(root=warehouse)
    overall = scorecard(a)
    assert np.isclose(
        sum(scorecard(g)["net_profit_usd"] for _, g in a.groupby("market")),
        overall["net_profit_usd"],
    )


def test_transaction_duplication_preserves_spend_and_n(warehouse):
    with connect(warehouse, read_only=False) as con:
        before = reconcile(con)
        con.begin()
        con.execute("INSERT INTO transactions SELECT * FROM transactions LIMIT 10")
        from pathlib import Path

        import investopt

        for file in sorted((Path(investopt.__file__).parent / "sql").glob("*.sql")):
            con.execute(file.read_text())
        after = reconcile(con)
        con.rollback()
        assert before["lead_count"] == after["lead_count"]
        assert before["experiment_count"] == after["experiment_count"]
        assert np.isclose(before["spend_mart_usd"], after["spend_mart_usd"], atol=1e-8)
