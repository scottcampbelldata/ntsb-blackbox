import urllib.parse

import httpx

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def build_query(make=None, model=None, city=None, state=None, year=None):
    """Build a GDELT free-text query for an accident. Year is accepted for call-site
    symmetry but GDELT relevance is driven by the aircraft/location terms."""
    parts = [p for p in (make, model) if p]
    parts.append("aviation accident")
    location = city or state
    if location:
        parts.append(location)
    return " ".join(str(p) for p in parts).strip()


def news_search_url(query):
    return "https://news.google.com/search?" + urllib.parse.urlencode({"q": query})


def _parse_articles(data):
    articles = []
    for item in data.get("articles") or []:
        if not item.get("url"):
            continue
        articles.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "domain": item.get("domain"),
                "date": item.get("seendate"),
            }
        )
    return articles


async def _gdelt_articles(query, max_records):
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": max_records,
        "sort": "hybridrel",
    }
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(GDELT_URL, params=params)
        response.raise_for_status()
        data = response.json()
    return _parse_articles(data)


async def fetch_related_coverage(*, make=None, model=None, city=None, state=None, year=None, max_records=5):
    query = build_query(make, model, city, state, year)
    search_url = news_search_url(query)
    try:
        articles = await _gdelt_articles(query, max_records)
        if articles:
            return {"query": query, "source": "gdelt", "articles": articles, "search_url": search_url}
    except Exception:
        pass
    return {"query": query, "source": "fallback", "articles": [], "search_url": search_url}
