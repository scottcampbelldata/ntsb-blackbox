# Redesign Plan 2 — Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Dashboard landing page — a KPI strip, a featured "accidents per year" hero chart, and a grid of the existing 7 analyses as cards with a "view SQL" expander — backed by new read-only endpoints that run every analysis through the existing SQL guard.

**Architecture:** The backend exposes the prebuilt analyses (from `src/sql_tool.py`) via `/api/analyses` and `/api/analyses/{key}`, executing each through `run_validated_query` and attaching a deterministically-built, validated Vega-Lite spec so the dashboard renders through the SAME `ChartView`/`vegaLiteToRecharts` contract as the Ask page. A single validated query powers `/api/dataset` (KPI figures). The frontend fetches these and composes the page from `KpiStrip` + `AnalysisCard` components.

**Tech Stack:** FastAPI, sqlglot guard, pytest (backend); React 19, Recharts, Vitest + Testing Library (frontend). Builds on Plan 1's `ChartView` and `vegaLiteToRecharts`.

## Global Constraints

- New backend endpoints are **read-only** and registered in `backend/app/main.py` alongside `ask_router`/`health_router`.
- Every analysis and KPI figure is produced by SQL run through `run_validated_query` (`backend/app/data/db.py`) — no raw, unvalidated queries.
- Analysis chart specs use the project's chart convention so they render via the existing adapter: a `line` mark for a year category (`x`=category ordinal, `y`=value quantitative); otherwise a horizontal `bar` (`x`=value quantitative, `y`=category nominal with `"sort": "-x"`). Specs must pass `validate_vega_lite_spec` (`src/chart_validator.py`).
- The 7 analysis keys come from `src/sql_tool.py` `ANALYSES` (do not redefine them): `accidents_by_year`, `top_makes`, `fatal_breakdown`, `accidents_by_phase`, `fatal_by_phase`, `accidents_by_state`, `weather_breakdown`. Each analysis row is `(category, value)` — `columns[0]` is the category, `columns[1]` the numeric value.
- The featured hero chart is `accidents_by_year`.
- KPI figures: `accident_count`, `fatal_count` (rows with `fatal_injury_count > 0`), `min_year`, `max_year`, `distinct_makes`.
- Frontend API base: `import.meta.env.VITE_API_BASE ?? ""`.
- React ^19, Vite ^6, TS ^5.7. Run frontend commands from `frontend/`; run pytest from the repo root.
- Numeric figures render with the `.tabular` class (tabular numerals) from Plan 1's `theme.css`.

---

## File Structure

Backend (`backend/app/`):
- `api/analyses.py` — new router: `/api/analyses`, `/api/analyses/{key}` (create).
- `api/dataset.py` — new router: `/api/dataset` KPIs (create).
- `main.py` — register both routers (modify).

Tests (`tests/`):
- `test_backend_analyses.py` — analyses endpoints (create).
- `test_backend_dataset.py` — dataset KPI endpoint (create).

Frontend (`frontend/src/`):
- `lib/api.ts` — typed dashboard API client + shared `API_BASE` (create).
- `components/KpiStrip.tsx` + `.test.tsx` (create).
- `components/AnalysisCard.tsx` + `.test.tsx` (create).
- `pages/Dashboard.tsx` — replace the placeholder; add `Dashboard.test.tsx` (modify/create).

---

## Task 1: Backend — analyses endpoints

**Files:**
- Create: `backend/app/api/analyses.py`
- Modify: `backend/app/main.py`
- Test: `tests/test_backend_analyses.py`

**Interfaces:**
- Consumes: `list_analyses`, `ANALYSES` from `sql_tool` (`src/sql_tool.py`); `run_validated_query` from `backend/app/data/db.py`; `validate_vega_lite_spec` from `chart_validator` (`src/chart_validator.py`).
- Produces:
  - `GET /api/analyses` → `{"analyses": [{"key": str, "label": str}, ...]}`
  - `GET /api/analyses/{key}` → `{"key": str, "label": str, "sql": str, "columns": [str], "rows": [obj], "chart_spec": obj}`; unknown key → HTTP 404.
  - `build_analysis_chart_spec(columns: list[str], *, title: str) -> dict` — deterministic validated Vega-Lite spec per the chart convention.

- [ ] **Step 1: Write failing tests**

Create `tests/test_backend_analyses.py`:

```python
import pytest
from fastapi.testclient import TestClient

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_backend_analyses.py -v`
Expected: FAIL — `/api/analyses` not found (404 from app) / import error.

- [ ] **Step 3: Implement the analyses router**

Create `backend/app/api/analyses.py`:

```python
from fastapi import APIRouter, HTTPException

from backend.app.data.db import run_validated_query
from chart_validator import validate_vega_lite_spec
from sql_tool import ANALYSES, list_analyses

router = APIRouter(prefix="/api")


def build_analysis_chart_spec(columns, *, title):
    """Build a validated Vega-Lite spec for a (category, value) analysis result,
    using the project chart convention: a line for a year category, otherwise a
    horizontal bar. Returns the validated spec, or None if the columns don't fit
    the (category, value) shape."""
    if len(columns) < 2:
        return None
    category, value = columns[0], columns[1]
    if category == "year":
        spec = {
            "mark": "line",
            "encoding": {
                "x": {"field": category, "type": "ordinal"},
                "y": {"field": value, "type": "quantitative"},
                "tooltip": [{"field": category}, {"field": value}],
            },
            "title": title,
        }
    else:
        spec = {
            "mark": "bar",
            "encoding": {
                "x": {"field": value, "type": "quantitative"},
                "y": {"field": category, "type": "nominal", "sort": "-x"},
                "tooltip": [{"field": category}, {"field": value}],
            },
            "title": title,
        }
    return validate_vega_lite_spec(spec, columns).spec


@router.get("/analyses")
def list_all_analyses():
    return {"analyses": [{"key": key, "label": label} for key, label in list_analyses()]}


@router.get("/analyses/{key}")
def run_analysis_endpoint(key: str):
    analysis = ANALYSES.get(key)
    if analysis is None:
        raise HTTPException(status_code=404, detail=f"Unknown analysis: {key}")
    result = run_validated_query(analysis["sql"])
    chart_spec = build_analysis_chart_spec(result.columns, title=analysis["label"])
    return {
        "key": key,
        "label": analysis["label"],
        "sql": result.sql,
        "columns": result.columns,
        "rows": result.rows,
        "chart_spec": chart_spec,
    }
```

- [ ] **Step 4: Register the router**

Modify `backend/app/main.py` — add the import and include it:

```python
from backend.app.api.analyses import router as analyses_router
```
and inside `create_app()`, after `app.include_router(ask_router)`:
```python
    app.include_router(analyses_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_backend_analyses.py -v`
Expected: PASS (DB-dependent tests pass if the local DB is built; otherwise they skip — the list and 404 tests must pass regardless).

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/analyses.py backend/app/main.py tests/test_backend_analyses.py
git commit -m "feat(backend): add analyses endpoints with validated chart specs"
```

---

## Task 2: Backend — dataset KPI endpoint

**Files:**
- Create: `backend/app/api/dataset.py`
- Modify: `backend/app/main.py`
- Test: `tests/test_backend_dataset.py`

**Interfaces:**
- Consumes: `run_validated_query` from `backend/app/data/db.py`.
- Produces: `GET /api/dataset` → `{"accident_count": int, "fatal_count": int, "min_year": int, "max_year": int, "distinct_makes": int}`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_backend_dataset.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_backend_dataset.py -v`
Expected: FAIL — `/api/dataset` returns 404 (route missing). (If no local DB, the test skips; in that case temporarily confirm the route is missing by `test_list_analyses`'s app — but the route-missing failure is the expected RED when the DB exists.)

- [ ] **Step 3: Implement the dataset router**

Create `backend/app/api/dataset.py`:

```python
from fastapi import APIRouter

from backend.app.data.db import run_validated_query

router = APIRouter(prefix="/api")

# One validated query produces every KPI. SUM(CASE ...) counts fatal accidents
# (fatal_injury_count > 0 is the reliable fatal signal in this dataset).
KPI_SQL = """
    SELECT
      COUNT(*) AS accident_count,
      SUM(CASE WHEN fatal_injury_count > 0 THEN 1 ELSE 0 END) AS fatal_count,
      MIN(event_year) AS min_year,
      MAX(event_year) AS max_year,
      COUNT(DISTINCT make) AS distinct_makes
    FROM accidents
"""


@router.get("/dataset")
def dataset_kpis():
    result = run_validated_query(KPI_SQL)
    row = result.rows[0]
    return {
        "accident_count": int(row["accident_count"] or 0),
        "fatal_count": int(row["fatal_count"] or 0),
        "min_year": int(row["min_year"]) if row["min_year"] is not None else None,
        "max_year": int(row["max_year"]) if row["max_year"] is not None else None,
        "distinct_makes": int(row["distinct_makes"] or 0),
    }
```

- [ ] **Step 4: Register the router**

Modify `backend/app/main.py` — add import and include:

```python
from backend.app.api.dataset import router as dataset_router
```
and inside `create_app()`, after `app.include_router(analyses_router)`:
```python
    app.include_router(dataset_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_backend_dataset.py tests/test_backend_analyses.py -v`
Expected: PASS (DB-dependent tests pass with a built DB, else skip; the analyses list/404 tests pass regardless).

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/dataset.py backend/app/main.py tests/test_backend_dataset.py
git commit -m "feat(backend): add dataset KPI endpoint"
```

---

## Task 3: Frontend — API client + KpiStrip

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/components/KpiStrip.tsx`
- Test: `frontend/src/components/KpiStrip.test.tsx`

**Interfaces:**
- Consumes: `ChartRow` from `src/lib/vegaLiteToRecharts`.
- Produces (`lib/api.ts`):
  - `const API_BASE: string`
  - `type AnalysisListItem = { key: string; label: string }`
  - `type AnalysisResult = { key: string; label: string; sql: string; columns: string[]; rows: ChartRow[]; chart_spec: Record<string, unknown> | null }`
  - `type DatasetKpis = { accident_count: number; fatal_count: number; min_year: number | null; max_year: number | null; distinct_makes: number }`
  - `async function fetchDataset(): Promise<DatasetKpis>`
  - `async function fetchAnalyses(): Promise<AnalysisListItem[]>`
  - `async function fetchAnalysis(key: string): Promise<AnalysisResult>`
- Produces (`KpiStrip.tsx`): `function KpiStrip(props: { kpis: DatasetKpis }): JSX.Element` — four tiles: Accidents (`accident_count`), Fatal (`fatal_count`), Years (`min_year`–`max_year`), Makes (`distinct_makes`). Figures use the `.tabular` class.

Note: `pages/Ask.tsx` keeps its own local `API_BASE` for now; unifying it onto `lib/api.ts` is deferred to Plan 3 (the Ask redesign) to avoid touching the working Ask flow here.

- [ ] **Step 1: Create the API client**

Create `frontend/src/lib/api.ts`:

```ts
import type { ChartRow } from "./vegaLiteToRecharts";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export type AnalysisListItem = { key: string; label: string };

export type AnalysisResult = {
  key: string;
  label: string;
  sql: string;
  columns: string[];
  rows: ChartRow[];
  chart_spec: Record<string, unknown> | null;
};

export type DatasetKpis = {
  accident_count: number;
  fatal_count: number;
  min_year: number | null;
  max_year: number | null;
  distinct_makes: number;
};

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchDataset(): Promise<DatasetKpis> {
  return getJson<DatasetKpis>("/api/dataset");
}

export async function fetchAnalyses(): Promise<AnalysisListItem[]> {
  const data = await getJson<{ analyses: AnalysisListItem[] }>("/api/analyses");
  return data.analyses;
}

export async function fetchAnalysis(key: string): Promise<AnalysisResult> {
  return getJson<AnalysisResult>(`/api/analyses/${key}`);
}
```

- [ ] **Step 2: Write the failing KpiStrip test**

Create `frontend/src/components/KpiStrip.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { KpiStrip } from "./KpiStrip";

const kpis = {
  accident_count: 12408,
  fatal_count: 2113,
  min_year: 2016,
  max_year: 2023,
  distinct_makes: 340
};

describe("KpiStrip", () => {
  it("renders all four KPI figures", () => {
    const { getByText } = render(<KpiStrip kpis={kpis} />);
    expect(getByText("12,408")).toBeInTheDocument();
    expect(getByText("2,113")).toBeInTheDocument();
    expect(getByText("2016–2023")).toBeInTheDocument();
    expect(getByText("340")).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run (from `frontend/`): `npm test -- KpiStrip`
Expected: FAIL — `KpiStrip` module missing.

- [ ] **Step 4: Implement KpiStrip**

Create `frontend/src/components/KpiStrip.tsx`:

```tsx
import type { DatasetKpis } from "../lib/api";

function Tile({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={`kpi-tile${accent ? " kpi-tile-accent" : ""}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value tabular">{value}</div>
    </div>
  );
}

export function KpiStrip({ kpis }: { kpis: DatasetKpis }) {
  const years =
    kpis.min_year != null && kpis.max_year != null ? `${kpis.min_year}–${kpis.max_year}` : "—";
  return (
    <div className="kpi-strip">
      <Tile label="Accidents" value={kpis.accident_count.toLocaleString("en-US")} />
      <Tile label="Fatal" value={kpis.fatal_count.toLocaleString("en-US")} accent />
      <Tile label="Years" value={years} />
      <Tile label="Makes" value={kpis.distinct_makes.toLocaleString("en-US")} />
    </div>
  );
}
```

- [ ] **Step 5: Run test to verify it passes**

Run (from `frontend/`): `npm test -- KpiStrip`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/components/KpiStrip.tsx frontend/src/components/KpiStrip.test.tsx
git commit -m "feat(frontend): add dashboard API client and KpiStrip"
```

---

## Task 4: Frontend — AnalysisCard

**Files:**
- Create: `frontend/src/components/AnalysisCard.tsx`
- Test: `frontend/src/components/AnalysisCard.test.tsx`

**Interfaces:**
- Consumes: `ChartView` from `./ChartView`; `AnalysisResult` from `../lib/api`.
- Produces: `function AnalysisCard(props: { analysis: AnalysisResult; featured?: boolean }): JSX.Element` — renders the label as a heading, the `ChartView` (from `chart_spec` + `rows`), and a `<details>` "View SQL" expander containing the `sql` in a `<pre>`. `featured` adds the `analysis-card-featured` class.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/AnalysisCard.test.tsx`:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { AnalysisCard } from "./AnalysisCard";
import type { AnalysisResult } from "../lib/api";

vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 800, height: 340 }}>{children}</div>
    )
  };
});

const analysis: AnalysisResult = {
  key: "top_makes",
  label: "Top aircraft makes by accident count",
  sql: "SELECT make, COUNT(*) AS accidents FROM accidents GROUP BY make LIMIT 15",
  columns: ["make", "accidents"],
  rows: [
    { make: "CESSNA", accidents: 300 },
    { make: "PIPER", accidents: 200 }
  ],
  chart_spec: {
    mark: "bar",
    encoding: {
      x: { field: "accidents", type: "quantitative" },
      y: { field: "make", type: "nominal" }
    }
  }
};

describe("AnalysisCard", () => {
  it("renders the label heading and a collapsed View SQL with the query", () => {
    const { getByRole, getByText } = render(<AnalysisCard analysis={analysis} />);
    expect(getByRole("heading", { name: analysis.label })).toBeInTheDocument();
    expect(getByText("View SQL")).toBeInTheDocument();
    expect(getByText(/SELECT make, COUNT/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `npm test -- AnalysisCard`
Expected: FAIL — `AnalysisCard` module missing.

- [ ] **Step 3: Implement AnalysisCard**

Create `frontend/src/components/AnalysisCard.tsx`:

```tsx
import { ChartView } from "./ChartView";
import type { AnalysisResult } from "../lib/api";

export function AnalysisCard({
  analysis,
  featured = false
}: {
  analysis: AnalysisResult;
  featured?: boolean;
}) {
  return (
    <section className={`analysis-card${featured ? " analysis-card-featured" : ""}`}>
      <h3 className="analysis-title">{analysis.label}</h3>
      <ChartView spec={analysis.chart_spec} rows={analysis.rows} />
      <details className="sql-disclosure">
        <summary>View SQL</summary>
        <pre>{analysis.sql}</pre>
      </details>
    </section>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run (from `frontend/`): `npm test -- AnalysisCard`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/AnalysisCard.tsx frontend/src/components/AnalysisCard.test.tsx
git commit -m "feat(frontend): add AnalysisCard with chart and view-SQL"
```

---

## Task 5: Frontend — Dashboard page

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/pages/Dashboard.test.tsx`
- Modify: `frontend/src/styles.css` (dashboard layout styles)

**Interfaces:**
- Consumes: `fetchDataset`, `fetchAnalyses`, `fetchAnalysis`, types from `../lib/api`; `KpiStrip`; `AnalysisCard`.
- Produces: `function Dashboard(): JSX.Element` — on mount fetches KPIs + the analyses list, then each analysis; renders `KpiStrip`, the `accidents_by_year` analysis as a featured `AnalysisCard`, and the rest in a grid. Shows a loading state while fetching and an error state on failure.

- [ ] **Step 1: Write the failing Dashboard test**

Create `frontend/src/pages/Dashboard.test.tsx`:

```tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 800, height: 340 }}>{children}</div>
    )
  };
});

vi.mock("../lib/api", () => ({
  fetchDataset: vi.fn(),
  fetchAnalyses: vi.fn(),
  fetchAnalysis: vi.fn()
}));

import { fetchDataset, fetchAnalyses, fetchAnalysis } from "../lib/api";
import { Dashboard } from "./Dashboard";

beforeEach(() => {
  vi.mocked(fetchDataset).mockResolvedValue({
    accident_count: 12408,
    fatal_count: 2113,
    min_year: 2016,
    max_year: 2023,
    distinct_makes: 340
  });
  vi.mocked(fetchAnalyses).mockResolvedValue([
    { key: "accidents_by_year", label: "Accidents per year" },
    { key: "top_makes", label: "Top aircraft makes by accident count" }
  ]);
  vi.mocked(fetchAnalysis).mockImplementation(async (key: string) => ({
    key,
    label: key === "accidents_by_year" ? "Accidents per year" : "Top aircraft makes by accident count",
    sql: "SELECT 1",
    columns: key === "accidents_by_year" ? ["year", "accidents"] : ["make", "accidents"],
    rows: [{ year: 2016, make: "CESSNA", accidents: 100 }],
    chart_spec: { mark: "bar", encoding: { x: { field: "accidents" }, y: { field: key === "accidents_by_year" ? "year" : "make" } } }
  }));
});

describe("Dashboard", () => {
  it("renders KPIs and an analysis card after loading", async () => {
    render(<Dashboard />);
    await waitFor(() => expect(screen.getByText("12,408")).toBeInTheDocument());
    expect(screen.getByRole("heading", { name: "Accidents per year" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `npm test -- Dashboard`
Expected: FAIL — current `Dashboard` is a placeholder with no KPIs; `getByText("12,408")` not found.

- [ ] **Step 3: Implement the Dashboard page**

Replace `frontend/src/pages/Dashboard.tsx`:

```tsx
import { useEffect, useState } from "react";
import { KpiStrip } from "../components/KpiStrip";
import { AnalysisCard } from "../components/AnalysisCard";
import { fetchAnalyses, fetchAnalysis, fetchDataset, type AnalysisResult, type DatasetKpis } from "../lib/api";

const HERO_KEY = "accidents_by_year";

export function Dashboard() {
  const [kpis, setKpis] = useState<DatasetKpis | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [dataset, list] = await Promise.all([fetchDataset(), fetchAnalyses()]);
        const results = await Promise.all(list.map((item) => fetchAnalysis(item.key)));
        if (cancelled) return;
        setKpis(dataset);
        setAnalyses(results);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load dashboard");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const hero = analyses.find((a) => a.key === HERO_KEY);
  const rest = analyses.filter((a) => a.key !== HERO_KEY);

  return (
    <div className="workspace">
      <section className="main-column">
        <h1 className="page-title">Dashboard</h1>
        <p className="subtitle">
          Question answering and analytics over NTSB aviation accident final reports. Every figure
          below is a real SQL query — expand “View SQL” on any chart to see exactly what produced it.
        </p>

        {loading && <div className="loading">Loading analytics…</div>}
        {error && <div className="error">{error}</div>}

        {kpis && <KpiStrip kpis={kpis} />}

        {hero && <AnalysisCard analysis={hero} featured />}

        {rest.length > 0 && (
          <div className="analysis-grid">
            {rest.map((analysis) => (
              <AnalysisCard key={analysis.key} analysis={analysis} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
```

- [ ] **Step 4: Add dashboard layout styles**

Append to `frontend/src/styles.css`:

```css
.page-title {
  font-family: var(--serif);
  font-size: 30px;
  margin: 0 0 4px;
}

.subtitle {
  color: var(--muted);
  line-height: 1.5;
  margin: 0 0 8px;
  max-width: 70ch;
}

.kpi-strip {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.kpi-tile {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-left: 3px solid var(--primary);
  border-radius: 8px;
  padding: 12px 14px;
}

.kpi-tile-accent {
  border-left-color: var(--danger);
}

.kpi-label {
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.kpi-value {
  font-size: 26px;
  font-weight: 800;
}

.analysis-card {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-radius: 8px;
  padding: 16px;
}

.analysis-title {
  font-family: var(--serif);
  font-size: 17px;
  margin: 0 0 10px;
}

.analysis-card-featured .chart-host {
  min-height: 380px;
}

.analysis-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

.sql-disclosure summary {
  color: var(--primary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  margin-top: 10px;
}

.loading {
  color: var(--muted);
  padding: 12px 0;
}

@media (max-width: 860px) {
  .kpi-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
```

- [ ] **Step 5: Run the Dashboard test to verify it passes**

Run (from `frontend/`): `npm test -- Dashboard`
Expected: PASS.

- [ ] **Step 6: Run the full suite and build**

Run (from `frontend/`): `npm test`
Expected: PASS — all suites (adapter, ChartView, useTheme, Navbar, App, KpiStrip, AnalysisCard, Dashboard).

Run (from `frontend/`): `npm run build`
Expected: build succeeds, no TypeScript errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/Dashboard.tsx frontend/src/pages/Dashboard.test.tsx frontend/src/styles.css
git commit -m "feat(frontend): build dashboard page with KPIs, hero, and analysis grid"
```

---

## Self-Review Notes

- **Spec coverage:** Dashboard analytics gallery (Tasks 1, 4, 5), KPI strip (Tasks 2, 3, 5), featured hero `accidents_by_year` (Task 5), view-SQL traceability (Task 4), charts via the existing `ChartView`/Vega-Lite contract (Task 1 builds validated specs; Task 4 renders them). All analyses run through `run_validated_query` (Tasks 1–2).
- **Chart convention consistency:** `build_analysis_chart_spec` (Task 1) emits the same `line`/horizontal-`bar` shapes the Plan 1 `vegaLiteToRecharts` adapter expects (verified against the adapter's role-flip: line→category=x, bar→category=y).
- **Placeholder scan:** none — every code step is complete.
- **Type consistency:** `AnalysisResult`/`DatasetKpis` defined in `lib/api.ts` (Task 3) are consumed unchanged by `KpiStrip` (Task 3), `AnalysisCard` (Task 4), and `Dashboard` (Task 5). Backend `/api/analyses/{key}` response (Task 1) matches the `AnalysisResult` fields. `/api/dataset` (Task 2) matches `DatasetKpis`.
- **Known deferral:** `pages/Ask.tsx` retains a local `API_BASE`; unifying onto `lib/api.ts` is Plan 3's job (avoids touching the working Ask flow here). Documented in Task 3.
```
