import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.context import gdelt


def test_build_query_combines_make_model_location():
    q = gdelt.build_query("Cessna", "172", "Reno", "NV", 2019)
    assert "Cessna" in q and "172" in q and "aviation accident" in q and "Reno" in q


def test_news_search_url_is_encoded():
    url = gdelt.news_search_url("Cessna 172 crash")
    assert url.startswith("https://news.google.com/search?")
    assert "Cessna" in url and "%20" in url or "+" in url


def test_parse_articles_keeps_only_urled_items():
    data = {"articles": [
        {"title": "A", "url": "https://x.com/a", "domain": "x.com", "seendate": "20190101"},
        {"title": "no url"},
    ]}
    parsed = gdelt._parse_articles(data)
    assert len(parsed) == 1
    assert parsed[0] == {"title": "A", "url": "https://x.com/a", "domain": "x.com", "date": "20190101"}


def test_context_endpoint_returns_gdelt_articles(monkeypatch):
    async def fake_articles(query, max_records):
        return [{"title": "Crash report", "url": "https://news.x/1", "domain": "news.x", "date": "20190101"}]
    monkeypatch.setattr(gdelt, "_gdelt_articles", fake_articles)

    client = TestClient(create_app())
    response = client.get("/api/context", params={"make": "Cessna", "city": "Reno"})
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "gdelt"
    assert data["articles"][0]["url"] == "https://news.x/1"
    assert data["search_url"].startswith("https://news.google.com/search?")


def test_context_endpoint_falls_back_on_error(monkeypatch):
    async def boom(query, max_records):
        raise RuntimeError("gdelt down")
    monkeypatch.setattr(gdelt, "_gdelt_articles", boom)

    client = TestClient(create_app())
    response = client.get("/api/context", params={"make": "Piper"})
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "fallback"
    assert data["articles"] == []
    assert data["search_url"].startswith("https://news.google.com/search?")


def test_context_endpoint_falls_back_on_empty(monkeypatch):
    async def empty(query, max_records):
        return []
    monkeypatch.setattr(gdelt, "_gdelt_articles", empty)

    client = TestClient(create_app())
    response = client.get("/api/context", params={"state": "OH"})
    assert response.json()["source"] == "fallback"
