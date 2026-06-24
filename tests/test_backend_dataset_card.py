from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_dataset_card_returns_provenance_without_requiring_db():
    client = TestClient(create_app())
    response = client.get("/api/dataset/card")
    assert response.status_code == 200
    card = response.json()

    assert card["source"]["name"]
    assert card["source"]["license"]
    assert card["coverage"]["start_year"] == 2016
    assert card["coverage"]["end_year"] == 2023
    assert any("2020" in gap for gap in card["coverage"]["known_gaps"])
    assert any("fatal_injury_count" in c for c in card["caveats"])

    # schema comes from schema_catalog and is non-empty with the documented fields
    assert len(card["schema"]) > 10
    first = card["schema"][0]
    assert {"name", "dtype", "description"} <= set(first)
    names = {col["name"] for col in card["schema"]}
    assert {"event_year", "make", "fatal_injury_count"} <= names

    # counts/ready come from get_data_status; present as keys regardless of DB
    assert "ready" in card
    assert "counts" in card
