# Black Box AI — Frontend Redesign & Feature Expansion

**Date:** 2026-06-23
**Status:** Approved design, ready for implementation planning

## Goal & Audience

A portfolio-grade redesign of the Black Box AI frontend, aimed at **senior data/analytics
engineering** reviewers (recruiters and hiring managers). The first impression is a polished
analytics dashboard; the through-line is **traceability and provenance** — every figure ties
back to visible SQL, every claim to a cited NTSB record.

The backend (FastAPI on a VPS) and data/retrieval core are kept; this work is the React
frontend ([frontend/](../../../frontend/)) plus the new read-only API endpoints the new pages need.

## Deployment Context (unchanged)

- Backend: FastAPI on a VPS.
- Frontend: Cloudflare Pages, building this repo's `frontend/`.
- `VITE_API_BASE` already points the frontend at the backend subdomain in production
  ([App.tsx](../../../frontend/src/App.tsx)); local dev stays relative via the Vite proxy.

## App Structure

A 3-page single-page app with a top navbar, using **React Router**:

- **Dashboard** (landing) — KPI strip + featured hero chart + grid of analyses.
- **Ask** — the redesigned natural-language tool (the current single-page flow).
- **Data** — dataset card / provenance.

The navbar also holds the **dark-mode toggle**.

## Visual System

Replaces the current flat [styles.css](../../../frontend/src/styles.css) with a token-based theme.

- **Light theme (default) — "Editorial":** white surfaces, serif headlines (Georgia / serif
  stack), hairline rules, body text in Inter. Accents: teal `#1f6f78` (primary), rust
  `#b3402f` (fatal / danger). Tabular numerals on all figures.
- **Dark theme — "Cockpit":** slate surfaces (`#0e1620` / `#16212e`), teal + amber accents.
- **Implementation:** CSS custom properties (design tokens) keyed off a `data-theme="light|dark"`
  attribute on `<html>`. One token file defines both themes. Toggle state persists to
  `localStorage` and respects `prefers-color-scheme` on first visit.

## Charts

Add **Recharts** as the charting library.

- A reusable `ChartView` component renders bar and line charts in both themes.
- **Ask flow:** a `vegaLiteToRecharts(spec)` adapter maps the backend's validated Vega-Lite
  spec onto Recharts props. The chart validator ([chart_validator.py](../../../src/chart_validator.py))
  already constrains specs to `bar`/`line` marks with `x`/`y` field encodings, so the mapping
  is small and bounded. The validated-spec contract is preserved; only the rendering changes.
  Replaces the hand-rolled CSS/SVG charts in
  [ResultPanels.tsx](../../../frontend/src/components/ResultPanels.tsx).
- **Dashboard:** cards render directly from each analysis's `{columns, rows}` payload.

## Page: Dashboard (featured hero + grid)

- **KPI strip:** total accidents, fatal accidents, year range (2016–2023), distinct makes.
- **Hero chart:** *Accidents per year* (line), full width.
- **Grid:** the other six analyses from [sql_tool.py](../../../src/sql_tool.py) as equal cards —
  top makes, fatal vs non-fatal, by phase of flight, fatal by phase, by state, by weather.
- **Per card:** a "view SQL" expander showing the exact query that produced it — the
  traceability hook.

## Page: Ask (answer + tabs; limitations always visible)

- **Lead:** answer text + route badge (`SQL` / `RETRIEVAL` / `BOTH`) + confidence percentage.
- **Chart** (when present) directly under the answer, via `ChartView`.
- **Tab bar:** SQL · Result Table · Citations · Audit trail.
- **Limitations:** always visible below the tabs (not hidden in a tab) — owning the caveats is
  part of the trust story.
- **Citations:** each shows the official NTSB record link (always present), plus a lazy-loaded
  **"Related coverage"** expander.

## Page: Data (dataset card / provenance)

Documents the dataset for a data-rigor audience:

- Source (Zenodo / NTSB), license (public domain), coverage window, **known gaps (2020–2021
  missing; recent years still filling in due to investigation lag)**.
- Row counts, schema/columns (from [schema_catalog.py](../../../src/schema_catalog.py)),
  latest ingest metadata.
- Honest notes on data caveats already documented in the codebase (manufacturer-name
  normalization is curated not complete; `highest_injury_level` corrupted on load so
  `fatal_injury_count > 0` is the fatal signal).

## News / External Context (senior-call decision)

- **Primary (always):** official NTSB record/docket links per citation. This is the provenance
  story.
- **Secondary (live):** related coverage via the **free, keyless GDELT API**, keyed off aircraft
  make/model + location + event year.
- **Fallback:** when GDELT returns nothing or is unavailable, render a constructed news-search
  deep-link so the UI is never empty.
- Fetched **lazily** when a user expands a citation's "Related coverage", so it never slows or
  blocks `/api/ask`.

Rationale: a paid news API key on an always-on public portfolio is an operational liability;
GDELT is free and demonstrates live external-data integration; the fallback + always-on official
links demonstrate robustness and provenance discipline.

## Backend Additions (new read-only endpoints)

All registered in [main.py](../../../backend/app/main.py) alongside the existing ask/health routers.

- `GET /api/analyses` → `[{key, label}, ...]` for the dashboard gallery.
- `GET /api/analyses/{key}` → `{sql, columns, rows}`, executed through the **existing SQL guard**
  (`run_validated_query` in [db.py](../../../backend/app/data/db.py)) so dashboard numbers are as
  traceable as Ask answers. Sources the queries from the existing
  [sql_tool.py](../../../src/sql_tool.py) `ANALYSES`.
- `GET /api/dataset` → KPI figures (total accidents, fatal count, year range, distinct makes);
  extends [status.py](../../../backend/app/data/status.py).
- `GET /api/dataset/card` → provenance payload: source, coverage, known gaps, row counts, schema,
  latest ingest.
- `GET /api/context?make=&model=&city=&state=&year=` → GDELT related-coverage lookup with graceful
  fallback to a constructed search link.

## Testing

- **Backend (pytest):**
  - `GET /api/analyses/{key}` runs each analysis through the guard and returns the expected shape.
  - `GET /api/dataset` and `GET /api/dataset/card` return the documented fields.
  - `GET /api/context` with a mocked GDELT response, and the fallback path when GDELT fails/empty.
- **Frontend:**
  - Unit-test `vegaLiteToRecharts` (the one piece with real logic).
  - Test theme persistence (toggle writes/reads `localStorage`, `data-theme` applied).
  - Keep other coverage light (presentational components).

## Out of Scope (YAGNI)

- Auth / user accounts.
- Saving, sharing, or permalinking answers.
- Real-time / scheduled data refresh from the UI.
- Photo or image galleries.
- A CMS or stored news articles (news stays on-demand links, never persisted).

## Component & File Map (orientation, not final)

Frontend (`frontend/src/`):

- `main.tsx` — add React Router.
- `theme/` — token CSS + `ThemeProvider` / toggle hook.
- `pages/Dashboard.tsx`, `pages/Ask.tsx`, `pages/Data.tsx`.
- `components/ChartView.tsx` + `lib/vegaLiteToRecharts.ts`.
- `components/Navbar.tsx`, `components/KpiStrip.tsx`, `components/AnalysisCard.tsx`,
  `components/Citation.tsx` (with related-coverage expander).
- Refactor `components/ResultPanels.tsx` into the tabbed Ask result.

Backend (`backend/app/`):

- `api/analyses.py`, `api/dataset.py`, `api/context.py` (new routers).
- `data/status.py` — extend for KPI aggregates.
- A GDELT client module under `backend/app/` (e.g. `context/gdelt.py`).
