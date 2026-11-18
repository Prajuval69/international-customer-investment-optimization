"""Whitelisted, parameterized dashboard queries; ratios recomputed from totals."""

from investopt.economics import financials
from investopt.warehouse import connect

ALLOWED = {
    "mart_campaign_month",
    "mart_acquisition_cohort",
    "mart_market_month",
    "mart_experiment_lead_outcomes",
    "mart_customer_checkpoint_90d",
    "markets",
}


def query(
    table="mart_campaign_month",
    root=None,
    markets=None,
    channels=None,
    start=None,
    end=None,
    mature=False,
):
    if table not in ALLOWED:
        raise ValueError("Unknown analytical table")
    clauses, parameters = [], []
    for column, values in [("market", markets), ("channel", channels)]:
        if values is not None:
            if len(values) == 0:
                clauses.append("FALSE")
            else:
                clauses.append(f"{column} IN ({','.join('?' for _ in values)})")
                parameters.extend(values)
    date_col = {
        "mart_experiment_lead_outcomes": "lead_month",
        "mart_customer_checkpoint_90d": "acquisition_cohort",
    }.get(table, "month_start")
    for op, value in [(">=", start), ("<=", end)]:
        if value is not None:
            clauses.append(f"{date_col} {op} ?")
            parameters.append(str(value))
    if mature:
        clauses.append("mature_270d" if table == "mart_customer_checkpoint_90d" else "mature_180d")
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connect(root) as con:
        return con.execute(f"SELECT * FROM {table}{where}", parameters).df()


def scorecard(frame):
    """Financial totals use mature campaign cohorts only, never partial margins."""
    frame = frame.loc[frame.mature_180d]
    totals = frame[
        [
            "lead_count",
            "converted_count",
            "contribution_180d_usd",
            "actual_spend_usd",
            "payout_cost_usd",
            "planned_spend_usd",
        ]
    ].sum()
    return financials(*totals)
