import pytest
from fastapi.testclient import TestClient

from sql_guard import validate_sql
from backend.app.api.dataset import KPI_SQL
from backend.app.main import create_app
from paths import DB_PATH


def test_kpi_sql_passes_guard():
    result = validate_sql(KPI_SQL)
    assert "accident_count" in result.sql
    assert "fatal_count" in result.sql


@pytest.mark.skipif(not DB_PATH.exists(), reason="local database not built")
def test_dataset_returns_kpi_figures():
    client = TestClient(create_app())
    response = client.get("/api/dataset")
    assert response.status_code == 200
    data = response.json()
    for field in ("accident_count", "fatal_count", "min_year", "max_year", "distinct_makes"):
        assert field in data
    assert data["accident_count"] > 0
    assert data["fatal_count"] >= 0
    if data["min_year"] is not None and data["max_year"] is not None:
        assert data["min_year"] <= data["max_year"]
    assert data["distinct_makes"] > 0
