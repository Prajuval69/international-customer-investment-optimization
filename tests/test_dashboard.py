from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from investopt.paths import paths

APP = Path(__file__).parents[1] / "app"
PAGES = [APP / "Home.py"] + sorted((APP / "pages").glob("*.py"))


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.stem)
def test_dashboard_pages_render(page, completed, monkeypatch):
    import app.components as components

    monkeypatch.setattr(components, "P", paths(completed))
    components.cached_query.clear()
    result = AppTest.from_file(str(page), default_timeout=30).run()
    assert not result.exception, [x.message for x in result.exception]
    assert result.title and "SIMULATED DATA" in result.caption[0].value


def test_dashboard_market_filter(completed, monkeypatch):
    import app.components as components

    monkeypatch.setattr(components, "P", paths(completed))
    components.cached_query.clear()
    app = AppTest.from_file(str(APP / "Home.py"), default_timeout=30).run()
    total = app.metric[0].value
    app.sidebar.multiselect[0].set_value(["IN"]).run()
    assert not app.exception and app.metric[0].value != total
    app.sidebar.multiselect[0].set_value([]).run()
    assert not app.exception and app.info


def test_dashboard_infeasible_budget(completed, monkeypatch):
    import app.components as components

    monkeypatch.setattr(components, "P", paths(completed))
    components.cached_query.clear()
    app = AppTest.from_file(str(APP / "pages/4_Investment_Optimizer.py"), default_timeout=30).run()
    app.number_input[0].set_value(9999999.0).run()
    assert not app.exception
    assert "Infeasible" in app.error[0].value


def test_dashboard_missing_data(tmp_path, monkeypatch):
    import app.components as components

    monkeypatch.setattr(components, "P", paths(tmp_path))
    app = AppTest.from_file(str(APP / "Home.py"), default_timeout=30).run()
    assert not app.exception and "demo --seed 42" in app.info[0].value
