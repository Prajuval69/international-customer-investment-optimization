"""Financial arithmetic in USD with aligned follow-up horizons."""

import math


def safe_ratio(numerator, denominator):
    """Return None for undefined denominators rather than infinity."""
    if denominator <= 0 or not math.isfinite(float(denominator)):
        return None
    return float(numerator / denominator)


def financials(leads, acquisitions, contribution, spend, payouts, planned):
    investment = spend + payouts
    profit = contribution - investment
    return {
        "leads": int(leads),
        "acquisitions": int(acquisitions),
        "contribution_usd": float(contribution),
        "campaign_spend_usd": float(spend),
        "payouts_usd": float(payouts),
        "investment_usd": float(investment),
        "net_profit_usd": float(profit),
        "cac_usd": safe_ratio(investment, acquisitions),
        "cohort_roi": safe_ratio(profit, investment),
        "conversion_rate": safe_ratio(acquisitions, leads),
        "utilization": safe_ratio(spend, planned),
        "contribution_to_cac_180d": safe_ratio(contribution, investment),
    }
