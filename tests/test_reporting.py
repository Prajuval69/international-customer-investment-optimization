import pandas as pd
import pytest

from investopt.demo import smoke


def test_real_report_outputs(completed):
    df = pd.read_csv(completed / "reports/kpi_scorecard.csv")
    assert df.lead_count.sum() == 1500
    assert "SIMULATED DATA" in df.data_classification.iloc[0]
    assert "synthetic executive report" in (completed / "reports/executive_summary.md").read_text(
        encoding="utf-8"
    )
    sheets = pd.read_excel(completed / "reports/analytics_report.xlsx", sheet_name=None)
    assert "Read me" in sheets and "Experiment" in sheets
    assert sheets["KPI scorecard"].lead_count.sum() == 1500


def test_smoke_artifacts(completed):
    result = smoke(completed)
    assert result["passed"] and result["row_counts"]["leads"] == 1500


def test_missing_smoke_guidance(tmp_path):
    with pytest.raises(ValueError, match="Run: python -m investopt demo"):
        smoke(tmp_path)
