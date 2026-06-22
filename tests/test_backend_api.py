import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from paths import DB_PATH


def test_health_endpoint_reports_ok():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.skipif(not DB_PATH.exists(), reason="local database not built")
def test_ask_endpoint_returns_sql_table_and_chart_for_analytics_question():
    client = TestClient(create_app())
    response = client.post(
        "/api/ask",
        json={
            "question": "Which phases of flight have the highest fatal accident counts, and show it as a chart?",
            "chart_preference": "auto",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"]["route"] == "chart"
    assert data["sql"]
    assert data["table"]["rows"]
    assert data["chart_spec"]
    assert data["audit"]


@pytest.mark.skipif(not DB_PATH.exists(), reason="local database not built")
def test_ask_endpoint_returns_chart_for_ohio_by_year():
    client = TestClient(create_app())
    response = client.post(
        "/api/ask",
        json={
            "question": "Show accidents in Ohio by year.",
            "chart_preference": "auto",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"]["route"] == "chart"
    assert data["table"]["rows"]
    assert data["chart_spec"]
    assert "Ohio" in data["sql"]


@pytest.mark.skipif(not DB_PATH.exists(), reason="local database not built")
def test_ask_endpoint_returns_chart_for_top_states_question():
    client = TestClient(create_app())
    response = client.post(
        "/api/ask",
        json={
            "question": "which states had the most reported incidents",
            "chart_preference": "auto",
            "session_id": "test-session",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route"]["route"] == "chart"
    assert data["table"]["rows"]
    assert data["chart_spec"]
