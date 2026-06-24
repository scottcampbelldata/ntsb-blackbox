import pytest
from fastapi.testclient import TestClient

from backend.app.api.analyses import build_analysis_chart_spec
from backend.app.main import create_app
from paths import DB_PATH


def test_list_analyses_returns_keys_and_labels():
    client = TestClient(create_app())
    response = client.get("/api/analyses")
    assert response.status_code == 200
    analyses = response.json()["analyses"]
    keys = {item["key"] for item in analyses}
    assert {"accidents_by_year", "top_makes", "weather_breakdown"} <= keys
    for item in analyses:
        assert item["label"]


def test_unknown_analysis_returns_404():
    client = TestClient(create_app())
    response = client.get("/api/analyses/not_a_real_key")
    assert response.status_code == 404


@pytest.mark.skipif(not DB_PATH.exists(), reason="local database not built")
def test_year_analysis_returns_line_spec_and_rows():
    client = TestClient(create_app())
    response = client.get("/api/analyses/accidents_by_year")
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "accidents_by_year"
    assert data["sql"]
    assert data["columns"][:2] == ["year", "accidents"]
    assert data["rows"]
    assert data["chart_spec"]["mark"] == "line"
    assert data["chart_spec"]["encoding"]["x"]["field"] == "year"


@pytest.mark.skipif(not DB_PATH.exists(), reason="local database not built")
def test_make_analysis_returns_horizontal_bar_spec():
    client = TestClient(create_app())
    response = client.get("/api/analyses/top_makes")
    assert response.status_code == 200
    spec = response.json()["chart_spec"]
    assert spec["mark"] == "bar"
    # horizontal bar: value on x (quantitative), category on y (nominal)
    assert spec["encoding"]["x"]["field"] == "accidents"
    assert spec["encoding"]["y"]["field"] == "make"


def test_chart_spec_year_produces_line():
    spec = build_analysis_chart_spec(["year", "accidents"], title="By Year")
    assert spec["mark"] == "line"
    assert spec["encoding"]["x"]["field"] == "year"
    assert spec["encoding"]["x"]["type"] == "ordinal"
    assert spec["encoding"]["y"]["field"] == "accidents"
    assert spec["encoding"]["y"]["type"] == "quantitative"


def test_chart_spec_non_year_produces_horizontal_bar():
    spec = build_analysis_chart_spec(["make", "accidents"], title="Top Makes")
    assert spec["mark"] == "bar"
    assert spec["encoding"]["x"]["field"] == "accidents"
    assert spec["encoding"]["x"]["type"] == "quantitative"
    assert spec["encoding"]["y"]["field"] == "make"
    assert spec["encoding"]["y"]["type"] == "nominal"
    assert spec["encoding"]["y"]["sort"] == "-x"


def test_chart_spec_too_few_columns_returns_none():
    assert build_analysis_chart_spec(["year"], title="Bad") is None
