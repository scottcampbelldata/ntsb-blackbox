# Redesign Plan 4 — Dataset Provenance Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Data page — a dataset provenance "card" documenting source, license, coverage window, known gaps, row counts, the column schema, honest data caveats, and the latest ingest — backed by a new `GET /api/dataset/card` endpoint.

**Architecture:** The endpoint assembles provenance from three sources: static descriptive constants (source/license/coverage/caveats, sourced from `docs/limitations.md` and the dataset README), the column schema from `src/schema_catalog.py` (`COLUMNS`), and live counts/ingest metadata from `get_data_status()` (which degrades gracefully when no DB is built). The frontend renders it as labeled sections + a schema table.

**Tech Stack:** FastAPI, pytest (backend); React 19, Vitest + Testing Library (frontend). Builds on Plan 2's `lib/api.ts` and the Data page placeholder from Plan 1.

## Global Constraints

- `GET /api/dataset/card` is read-only, added to the existing dataset router (`backend/app/api/dataset.py`).
- The card must return useful provenance EVEN WITHOUT a built database: source/coverage/caveats/schema are static or from `schema_catalog`; counts/ingest come from `get_data_status()` and are null/absent when the DB isn't ready.
- Schema rows come from `schema_catalog.COLUMNS` — each `{name, dtype, description}`. Do not hand-duplicate the column list.
- Caveats are sourced from `docs/limitations.md` (2020–2021 absent; recent years incomplete due to investigation lag; `highest_injury_level` corrupted so `fatal_injury_count > 0` is the fatal signal; curated manufacturer-name normalization; multi-aircraft concatenated fields).
- Coverage window: start_year 2016, end_year 2023.
- Frontend uses `lib/api.ts` (the shared client) and theme tokens for styling.
- React ^19, Vite ^6, TS ^5.7. Run frontend commands from `frontend/`; pytest from the repo root.

---

## File Structure

Backend (`backend/app/`):
- `api/dataset.py` — add the `/dataset/card` route + provenance constants (modify).

Tests (`tests/`):
- `test_backend_dataset_card.py` — card endpoint (create).

Frontend (`frontend/src/`):
- `lib/api.ts` — add `SchemaColumn`, `DatasetCard` types + `fetchDatasetCard()` (modify).
- `pages/Data.tsx` — replace the placeholder with the provenance card (modify) + `Data.test.tsx` (create).
- `styles.css` — data-card styles (modify).

---

## Task 1: Backend — dataset card endpoint

**Files:**
- Modify: `backend/app/api/dataset.py`
- Test: `tests/test_backend_dataset_card.py`

**Interfaces:**
- Consumes: `get_data_status` from `backend/app/data/status.py`; `COLUMNS`, `TABLE_NAME` from `schema_catalog` (`src/schema_catalog.py`).
- Produces: `GET /api/dataset/card` → `{source:{name,provider,license}, coverage:{start_year,end_year,known_gaps[]}, caveats[], table, schema:[{name,dtype,description}], counts:{accident_count,tracked_source_count}, database, ready, latest_ingest}`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_backend_dataset_card.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_backend_dataset_card.py -v`
Expected: FAIL — `/api/dataset/card` returns 404 (route missing).

- [ ] **Step 3: Implement the card endpoint**

In `backend/app/api/dataset.py`, add imports at the top (alongside the existing `run_validated_query` import):

```python
from backend.app.data.status import get_data_status
from schema_catalog import COLUMNS, TABLE_NAME
```

Then add the provenance constants and route (after the existing `dataset_kpis` function):

```python
DATASET_SOURCE = {
    "name": "US NTSB aviation accident final reports",
    "provider": "NTSB, loaded from a public Zenodo dataset",
    "license": "Public domain (US government work)",
}

COVERAGE = {
    "start_year": 2016,
    "end_year": 2023,
    "known_gaps": [
        "2020 and 2021 are absent from this dataset.",
        "Recent years can be incomplete because NTSB final reports take time to publish.",
    ],
}

CAVEATS = [
    "The loaded corpus is not every aviation accident.",
    "Manufacturer names are normalized with a curated alias list (casing plus a few "
    "high-volume merges), not a complete entity-resolution solution.",
    "highest_injury_level was corrupted to nulls on load; fatal_injury_count > 0 is the "
    "reliable fatal signal.",
    "Multi-aircraft records can concatenate values in fields such as number_of_engines.",
]


@router.get("/dataset/card")
def dataset_card():
    status = get_data_status()
    return {
        "source": DATASET_SOURCE,
        "coverage": COVERAGE,
        "caveats": CAVEATS,
        "table": TABLE_NAME,
        "schema": [
            {"name": col.name, "dtype": col.dtype, "description": col.description}
            for col in COLUMNS
        ],
        "counts": {
            "accident_count": status.get("accident_count"),
            "tracked_source_count": status.get("tracked_source_count"),
        },
        "database": status.get("database"),
        "ready": status.get("ready", False),
        "latest_ingest": status.get("latest_ingest"),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_backend_dataset_card.py -v`
Expected: PASS (no DB required — counts are null/absent but the structure is present).

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/dataset.py tests/test_backend_dataset_card.py
git commit -m "feat(backend): add dataset provenance card endpoint"
```

---

## Task 2: Frontend — API client + Data page

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/pages/Data.tsx`
- Test: `frontend/src/pages/Data.test.tsx`

**Interfaces:**
- Produces (`lib/api.ts`):
  - `type SchemaColumn = { name: string; dtype: string; description: string }`
  - `type DatasetCard = { source: { name: string; provider: string; license: string }; coverage: { start_year: number; end_year: number; known_gaps: string[] }; caveats: string[]; table: string; schema: SchemaColumn[]; counts: { accident_count: number | null; tracked_source_count: number | null }; database: string | null; ready: boolean; latest_ingest: Record<string, unknown> | null }`
  - `async function fetchDatasetCard(): Promise<DatasetCard>`
- Produces (`pages/Data.tsx`): `function Data(): JSX.Element` — fetches the card on mount; renders source/license, coverage + known-gaps, counts (when ready), a schema table, and caveats; loading + error states.

- [ ] **Step 1: Add the API client method**

Append to `frontend/src/lib/api.ts`:

```ts
export type SchemaColumn = { name: string; dtype: string; description: string };

export type DatasetCard = {
  source: { name: string; provider: string; license: string };
  coverage: { start_year: number; end_year: number; known_gaps: string[] };
  caveats: string[];
  table: string;
  schema: SchemaColumn[];
  counts: { accident_count: number | null; tracked_source_count: number | null };
  database: string | null;
  ready: boolean;
  latest_ingest: Record<string, unknown> | null;
};

export async function fetchDatasetCard(): Promise<DatasetCard> {
  return getJson<DatasetCard>("/api/dataset/card");
}
```

- [ ] **Step 2: Write the failing Data page test**

Create `frontend/src/pages/Data.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

vi.mock("../lib/api", () => ({ fetchDatasetCard: vi.fn() }));

import { fetchDatasetCard } from "../lib/api";
import { Data } from "./Data";

beforeEach(() => {
  vi.mocked(fetchDatasetCard).mockResolvedValue({
    source: { name: "US NTSB aviation accident final reports", provider: "NTSB via Zenodo", license: "Public domain" },
    coverage: { start_year: 2016, end_year: 2023, known_gaps: ["2020 and 2021 are absent from this dataset."] },
    caveats: ["fatal_injury_count > 0 is the reliable fatal signal."],
    table: "accidents",
    schema: [
      { name: "event_year", dtype: "INTEGER", description: "Year extracted from event_date." },
      { name: "make", dtype: "TEXT", description: "Aircraft make/manufacturer as reported." }
    ],
    counts: { accident_count: 12408, tracked_source_count: null },
    database: "sqlite",
    ready: true,
    latest_ingest: null
  });
});

describe("Data page", () => {
  it("renders provenance, a known gap, a schema row, and a caveat", async () => {
    render(<Data />);
    await waitFor(() =>
      expect(screen.getByText("US NTSB aviation accident final reports")).toBeInTheDocument()
    );
    expect(screen.getByText(/2020 and 2021 are absent/)).toBeInTheDocument();
    expect(screen.getByText("event_year")).toBeInTheDocument();
    expect(screen.getByText(/reliable fatal signal/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run (from `frontend/`): `npm test -- Data`
Expected: FAIL — current `Data` is the placeholder; the source name / schema row are absent.

- [ ] **Step 4: Implement the Data page**

Replace `frontend/src/pages/Data.tsx`:

```tsx
import { useEffect, useState } from "react";
import { fetchDatasetCard, type DatasetCard } from "../lib/api";

export function Data() {
  const [card, setCard] = useState<DatasetCard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchDatasetCard()
      .then((data) => {
        if (!cancelled) setCard(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load dataset card");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="workspace">
      <section className="main-column">
        <h1 className="page-title">Data</h1>
        <p className="subtitle">
          Provenance and known limits of the corpus behind every answer. Being explicit about what
          the data does and doesn't cover is part of trusting the numbers.
        </p>

        {loading && <div className="loading">Loading dataset card…</div>}
        {error && <div className="error">{error}</div>}

        {card && (
          <>
            <section className="card-block">
              <h2>Source</h2>
              <p className="source-name">{card.source.name}</p>
              <dl className="meta-list">
                <div><dt>Provider</dt><dd>{card.source.provider}</dd></div>
                <div><dt>License</dt><dd>{card.source.license}</dd></div>
                <div><dt>Coverage</dt><dd className="tabular">{card.coverage.start_year}–{card.coverage.end_year}</dd></div>
                {card.ready && card.counts.accident_count != null && (
                  <div><dt>Rows</dt><dd className="tabular">{card.counts.accident_count.toLocaleString("en-US")}</dd></div>
                )}
              </dl>
            </section>

            <section className="card-block">
              <h2>Known gaps</h2>
              <ul className="gap-list">
                {card.coverage.known_gaps.map((gap) => <li key={gap}>{gap}</li>)}
              </ul>
            </section>

            <section className="card-block">
              <h2>Schema — <code>{card.table}</code></h2>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr><th>Column</th><th>Type</th><th>Description</th></tr>
                  </thead>
                  <tbody>
                    {card.schema.map((col) => (
                      <tr key={col.name}>
                        <td><code>{col.name}</code></td>
                        <td>{col.dtype}</td>
                        <td>{col.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="card-block">
              <h2>Caveats</h2>
              <ul className="gap-list">
                {card.caveats.map((caveat) => <li key={caveat}>{caveat}</li>)}
              </ul>
            </section>
          </>
        )}
      </section>
    </div>
  );
}
```

- [ ] **Step 5: Run test to verify it passes**

Run (from `frontend/`): `npm test -- Data`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/pages/Data.tsx frontend/src/pages/Data.test.tsx
git commit -m "feat(frontend): build dataset provenance Data page"
```

---

## Task 3: Data page styling + full verification

**Files:**
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Add the data-card styles**

Append to `frontend/src/styles.css`:

```css
.card-block {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-radius: 8px;
  margin-top: 12px;
  padding: 16px;
}

.card-block h2 {
  font-family: var(--serif);
  font-size: 18px;
  margin: 0 0 12px;
}

.source-name {
  font-size: 17px;
  font-weight: 700;
  margin: 0 0 12px;
}

.meta-list {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  margin: 0;
}

.meta-list dt {
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.meta-list dd {
  font-size: 16px;
  font-weight: 700;
  margin: 2px 0 0;
}

.gap-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding-left: 18px;
}

.gap-list li {
  color: var(--text);
  line-height: 1.5;
}

.card-block code {
  background: var(--bg);
  border-radius: 4px;
  font-size: 13px;
  padding: 1px 5px;
}
```

- [ ] **Step 2: Run the full suite**

Run (from `frontend/`): `npm test`
Expected: PASS — all suites including `Data`, plus Plan 1–3 suites.

- [ ] **Step 3: Build**

Run (from `frontend/`): `npm run build`
Expected: build succeeds, no TS errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/styles.css
git commit -m "style(frontend): theme the dataset provenance card"
```

---

## Self-Review Notes

- **Spec coverage:** source/license (Task 1–2), coverage window + known gaps (Task 1–2), row counts when ready (Task 2), schema from `schema_catalog` (Task 1 endpoint, Task 2 table), honest caveats (Task 1–2). Endpoint works without a DB (Task 1 test asserts this).
- **DRY:** schema is generated from `schema_catalog.COLUMNS`, not duplicated. The Data page reuses the shared `getJson`/`lib/api.ts` client and the existing `.table-scroll`/`table` styles.
- **Placeholder scan:** none — every code step is complete.
- **Type consistency:** `DatasetCard`/`SchemaColumn` (Task 2) match the endpoint payload (Task 1) field-for-field; `fetchDatasetCard` uses the existing `getJson` helper.
- **Deferred to Plan 5:** none — the Data page is self-contained; News is independent.
```
