import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from paths import DB_PATH


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
    assert data["min_year"] <= data["max_year"]
    assert data["distinct_makes"] > 0
