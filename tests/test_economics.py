import pytest

from investopt.economics import financials, safe_ratio


def test_golden_economics():
    f = financials(10, 2, 180, 100, 20, 80)
    assert f["cac_usd"] == 60 and f["cohort_roi"] == 0.5
    assert f["net_profit_usd"] == 60 and f["conversion_rate"] == 0.2
    assert f["utilization"] == 1.25


@pytest.mark.parametrize("denominator", [0, -1, float("inf")])
def test_safe_denominator(denominator):
    assert safe_ratio(100, denominator) is None
