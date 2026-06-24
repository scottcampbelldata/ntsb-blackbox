# Redesign Plan 5 — Related Coverage (GDELT News) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add live "related coverage" to each Ask citation — a `GET /api/context` endpoint that queries the free, keyless GDELT news API for an accident and gracefully falls back to a constructed news-search link, surfaced by a lazy-loading "Related coverage" expander on each citation.

**Architecture:** A small `backend/app/context/gdelt.py` module isolates the GDELT call behind testable pure helpers (`build_query`, `news_search_url`, `_parse_articles`) and a single network function (`_gdelt_articles`, using `httpx.AsyncClient` per the codebase convention). `fetch_related_coverage` returns GDELT articles when available, else a `fallback` result that always carries a `search_url`. The frontend `CitationCoverage` component lazily calls `/api/context` the first time a user expands it, so `/api/ask` is never slowed.

**Tech Stack:** FastAPI + httpx, pytest (backend); React 19, Vitest + Testing Library (frontend). Builds on Plan 2's `lib/api.ts` and Plan 3's `ResultPanels`/Citations.

## Global Constraints

- `GET /api/context` is read-only, registered in `backend/app/main.py`. Query params: `make`, `model`, `city`, `state` (strings, optional), `year` (int, optional).
- GDELT is free and KEYLESS — no API key, no secret. Use `httpx.AsyncClient` with a short timeout (5s).
- The endpoint NEVER errors out to the client: on any GDELT failure or empty result it returns a `fallback` result with `articles: []` and a constructed `search_url` (Google News query). `source` is `"gdelt"` or `"fallback"`.
- The network call is isolated in `_gdelt_articles` so tests mock it — tests make NO live network calls.
- Related coverage is fetched LAZILY on the frontend (first expand only), never as part of `/api/ask`.
- The primary citation link (NTSB `report_url`, from Plan 3) stays; this adds a secondary coverage expander.
- React ^19, Vite ^6, TS ^5.7. Run frontend commands from `frontend/`; pytest from the repo root.

---

## File Structure

Backend (`backend/app/`):
- `context/__init__.py` (create, empty).
- `context/gdelt.py` — query building, GDELT fetch, fallback (create).
- `api/context.py` — `/api/context` router (create).
- `main.py` — register the context router (modify).

Tests (`tests/`):
- `test_backend_context.py` — pure helpers + endpoint (gdelt + fallback paths, mocked) (create).

Frontend (`frontend/src/`):
- `lib/api.ts` — `RelatedArticle`/`RelatedCoverage`/`ContextParams` types + `fetchContext()` (modify).
- `components/CitationCoverage.tsx` + `CitationCoverage.test.tsx` (create).
- `components/ResultPanels.tsx` — render `CitationCoverage` per citation (modify).
- `styles.css` — coverage styles (modify).

---

## Task 1: Backend — GDELT module + context endpoint

**Files:**
- Create: `backend/app/context/__init__.py` (empty)
- Create: `backend/app/context/gdelt.py`
- Create: `backend/app/api/context.py`
- Modify: `backend/app/main.py`
- Test: `tests/test_backend_context.py`

**Interfaces:**
- Produces (`context/gdelt.py`):
  - `build_query(make, model, city, state, year) -> str`
  - `news_search_url(query) -> str`
  - `_parse_articles(data: dict) -> list[dict]`
  - `async def _gdelt_articles(query, max_records) -> list[dict]` (network; mocked in tests)
  - `async def fetch_related_coverage(*, make=None, model=None, city=None, state=None, year=None, max_records=5) -> dict` → `{query, source, articles, search_url}`
- Produces: `GET /api/context?make=&model=&city=&state=&year=` → the `fetch_related_coverage` result.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_backend_context.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_backend_context.py -v`
Expected: FAIL — `backend.app.context` does not exist / `/api/context` 404.

- [ ] **Step 3: Implement the GDELT module**

Create `backend/app/context/__init__.py` (empty file).

Create `backend/app/context/gdelt.py`:

```python
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
```

- [ ] **Step 4: Implement the endpoint and register it**

Create `backend/app/api/context.py`:

```python
from fastapi import APIRouter

from backend.app.context.gdelt import fetch_related_coverage

router = APIRouter(prefix="/api")


@router.get("/context")
async def context(
    make: str | None = None,
    model: str | None = None,
    city: str | None = None,
    state: str | None = None,
    year: int | None = None,
):
    return await fetch_related_coverage(make=make, model=model, city=city, state=state, year=year)
```

Modify `backend/app/main.py` — add import and include:

```python
from backend.app.api.context import router as context_router
```
and inside `create_app()`, after `app.include_router(dataset_router)`:
```python
    app.include_router(context_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_backend_context.py -v`
Expected: PASS — all six tests (no live network; the endpoint tests monkeypatch `_gdelt_articles`).

- [ ] **Step 6: Commit**

```bash
git add backend/app/context backend/app/api/context.py backend/app/main.py tests/test_backend_context.py
git commit -m "feat(backend): add GDELT related-coverage context endpoint with fallback"
```

---

## Task 2: Frontend — fetchContext + CitationCoverage + wire into ResultPanels

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/components/CitationCoverage.tsx`
- Test: `frontend/src/components/CitationCoverage.test.tsx`
- Modify: `frontend/src/components/ResultPanels.tsx`

**Interfaces:**
- Produces (`lib/api.ts`):
  - `type RelatedArticle = { title: string | null; url: string | null; domain: string | null; date: string | null }`
  - `type RelatedCoverage = { query: string; source: "gdelt" | "fallback"; articles: RelatedArticle[]; search_url: string }`
  - `type ContextParams = { make?: string; model?: string; city?: string; state?: string; year?: number }`
  - `async function fetchContext(params: ContextParams): Promise<RelatedCoverage>`
- Produces: `function CitationCoverage(props: { citation: AskResponse["citations"][number] }): JSX.Element` — a button that, on first expand, lazily fetches `/api/context` for the citation and renders the article list (or the `search_url` link when empty).

- [ ] **Step 1: Add fetchContext to the API client**

Append to `frontend/src/lib/api.ts`:

```ts
export type RelatedArticle = { title: string | null; url: string | null; domain: string | null; date: string | null };

export type RelatedCoverage = {
  query: string;
  source: "gdelt" | "fallback";
  articles: RelatedArticle[];
  search_url: string;
};

export type ContextParams = { make?: string; model?: string; city?: string; state?: string; year?: number };

export async function fetchContext(params: ContextParams): Promise<RelatedCoverage> {
  const qs = new URLSearchParams();
  if (params.make) qs.set("make", params.make);
  if (params.model) qs.set("model", params.model);
  if (params.city) qs.set("city", params.city);
  if (params.state) qs.set("state", params.state);
  if (params.year != null) qs.set("year", String(params.year));
  return getJson<RelatedCoverage>(`/api/context?${qs.toString()}`);
}
```

- [ ] **Step 2: Write the failing CitationCoverage test**

Create `frontend/src/components/CitationCoverage.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("../lib/api", () => ({ fetchContext: vi.fn() }));

import { fetchContext } from "../lib/api";
import { CitationCoverage } from "./CitationCoverage";

const citation = {
  ntsb_no: "ABC123",
  score: 0.9,
  matched_passage: "…",
  probable_cause: "pilot error",
  make: "Cessna",
  city: "Reno"
};

beforeEach(() => vi.mocked(fetchContext).mockReset());

describe("CitationCoverage", () => {
  it("does not fetch until expanded, then lists articles", async () => {
    vi.mocked(fetchContext).mockResolvedValue({
      query: "Cessna aviation accident Reno",
      source: "gdelt",
      articles: [{ title: "Crash report", url: "https://news.x/1", domain: "news.x", date: "20190101" }],
      search_url: "https://news.google.com/search?q=x"
    });

    render(<CitationCoverage citation={citation} />);
    expect(fetchContext).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /related coverage/i }));
    await waitFor(() => expect(screen.getByText("Crash report")).toBeInTheDocument());
    expect(fetchContext).toHaveBeenCalledTimes(1);
  });

  it("shows a search link when there are no articles", async () => {
    vi.mocked(fetchContext).mockResolvedValue({
      query: "Piper aviation accident",
      source: "fallback",
      articles: [],
      search_url: "https://news.google.com/search?q=piper"
    });

    render(<CitationCoverage citation={citation} />);
    fireEvent.click(screen.getByRole("button", { name: /related coverage/i }));
    await waitFor(() => expect(screen.getByRole("link", { name: /search news/i })).toBeInTheDocument());
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run (from `frontend/`): `npm test -- CitationCoverage`
Expected: FAIL — `CitationCoverage` module missing.

- [ ] **Step 4: Implement CitationCoverage**

Create `frontend/src/components/CitationCoverage.tsx`:

```tsx
import { useState } from "react";
import { fetchContext, type RelatedCoverage } from "../lib/api";
import type { AskResponse } from "../types";

export function CitationCoverage({ citation }: { citation: AskResponse["citations"][number] }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<RelatedCoverage | null>(null);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && !loaded) {
      setLoading(true);
      try {
        const result = await fetchContext({
          make: citation.make,
          model: citation.model,
          city: citation.city,
          state: citation.state,
          year: citation.event_year
        });
        setData(result);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
        setLoaded(true);
      }
    }
  }

  return (
    <div className="coverage">
      <button type="button" className="coverage-toggle" aria-expanded={open} onClick={toggle}>
        Related coverage
      </button>
      {open && (
        <div className="coverage-body">
          {loading && <span className="coverage-loading">Loading…</span>}
          {!loading && data && data.articles.length > 0 && (
            <ul className="coverage-list">
              {data.articles.map((article, index) => (
                <li key={article.url ?? index}>
                  {article.url ? (
                    <a href={article.url} target="_blank" rel="noreferrer">
                      {article.title || article.domain || article.url}
                    </a>
                  ) : (
                    <span>{article.title || ""}</span>
                  )}
                  {article.domain && <span className="coverage-domain"> · {article.domain}</span>}
                </li>
              ))}
            </ul>
          )}
          {!loading && data && data.articles.length === 0 && (
            <a className="coverage-search" href={data.search_url} target="_blank" rel="noreferrer">
              Search news for this accident
            </a>
          )}
          {!loading && !data && <span className="coverage-empty">Coverage unavailable.</span>}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Run test to verify it passes**

Run (from `frontend/`): `npm test -- CitationCoverage`
Expected: PASS.

- [ ] **Step 6: Wire CitationCoverage into ResultPanels**

In `frontend/src/components/ResultPanels.tsx`, import it and render it inside each citation. Add the import:

```tsx
import { CitationCoverage } from "./CitationCoverage";
```

In the `Citations` sub-component, add `<CitationCoverage citation={c} />` as the last child of each `<article className="citation">`, after the `<p>`:

```tsx
        <article key={c.ntsb_no} className="citation">
          {c.report_url ? (
            <a href={c.report_url} target="_blank" rel="noreferrer">{c.ntsb_no}</a>
          ) : (
            <span className="citation-id">{c.ntsb_no}</span>
          )}
          <p>{c.probable_cause || c.matched_passage}</p>
          <CitationCoverage citation={c} />
        </article>
```

- [ ] **Step 7: Run the suite to verify nothing regressed**

Run (from `frontend/`): `npm test -- ResultPanels CitationCoverage`
Expected: PASS — ResultPanels still renders citations; CitationCoverage tests green.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/components/CitationCoverage.tsx frontend/src/components/CitationCoverage.test.tsx frontend/src/components/ResultPanels.tsx
git commit -m "feat(frontend): add lazy related-coverage expander to citations"
```

---

## Task 3: Coverage styling + full verification

**Files:**
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Add the coverage styles**

Append to `frontend/src/styles.css`:

```css
.coverage {
  margin-top: 8px;
}

.coverage-toggle {
  background: transparent;
  border: none;
  color: var(--primary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  padding: 0;
}

.coverage-body {
  margin-top: 8px;
}

.coverage-list {
  display: grid;
  gap: 6px;
  margin: 0;
  padding-left: 18px;
}

.coverage-list a {
  color: var(--primary);
}

.coverage-domain {
  color: var(--muted);
  font-size: 12px;
}

.coverage-loading,
.coverage-empty {
  color: var(--muted);
  font-size: 13px;
}

.coverage-search {
  color: var(--primary);
  font-size: 13px;
  font-weight: 600;
}
```

- [ ] **Step 2: Run the full suite**

Run (from `frontend/`): `npm test`
Expected: PASS — all suites including `CitationCoverage`, plus Plan 1–4 suites.

- [ ] **Step 3: Build**

Run (from `frontend/`): `npm run build`
Expected: build succeeds, no TS errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/styles.css
git commit -m "style(frontend): theme the related-coverage expander"
```

---

## Self-Review Notes

- **Spec coverage:** GDELT free/keyless lookup (Task 1 `_gdelt_articles`), graceful fallback with always-present `search_url` (Task 1 `fetch_related_coverage`), NTSB link stays primary + coverage is secondary/lazy (Task 2 wiring), lazy fetch on first expand only (Task 2 `CitationCoverage`).
- **Testability:** the network call is isolated in `_gdelt_articles` and monkeypatched, so backend tests cover the gdelt, error-fallback, and empty-fallback paths with no live network; pure helpers tested directly.
- **Placeholder scan:** none — every code step is complete.
- **Type consistency:** `RelatedCoverage`/`RelatedArticle` (Task 2) match the endpoint payload (Task 1) field-for-field; `CitationCoverage` consumes `AskResponse["citations"][number]` (existing type) and passes make/model/city/state/event_year to `fetchContext`.
- **No `/api/ask` change:** coverage is entirely lazy and additive; the ask flow and its contract are untouched.
```
