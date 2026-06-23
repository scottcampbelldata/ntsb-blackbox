# Redesign Plan 1 — Foundation (Theme, Router, Charts) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the shared frontend foundation for the redesign — a Vite test runner, a Vega-Lite→Recharts chart adapter, a reusable `ChartView`, the Editorial/Cockpit theme system with a dark-mode toggle, and a React Router app shell with Dashboard/Ask/Data pages.

**Architecture:** Pure logic (the chart adapter, the theme hook) is unit-tested; presentational components get light smoke coverage. The existing single-page Ask flow in `App.tsx` is moved verbatim into `pages/Ask.tsx` so nothing regresses, then wrapped in a router shell with a navbar. Theme is driven by CSS custom properties keyed off `data-theme` on `<html>`.

**Tech Stack:** React 19, Vite 6, TypeScript 5.7, React Router v7 (`react-router-dom`), Recharts, Vitest + Testing Library + jsdom.

## Global Constraints

- React `^19.0.0`, Vite `^6.0.0`, TypeScript `^5.7.0` — do not change these floors.
- Theme accents (exact values): primary teal `#1f6f78`, danger/fatal rust `#b3402f`; dark surfaces `#0e1620` (page) and `#16212e` (card), dark accent amber `#e6a23c`.
- All numeric figures render with `font-variant-numeric: tabular-nums`.
- Theme is selected via a `data-theme="light"|"dark"` attribute on `<html>`; default light, persisted to `localStorage` under key `blackbox-theme`, first-visit value from `prefers-color-scheme`.
- API base comes from `import.meta.env.VITE_API_BASE ?? ""` (relative in dev so the Vite proxy applies). Never hardcode a backend URL.
- Run all frontend commands from the `frontend/` directory.

---

## File Structure

Frontend (`frontend/`):
- `package.json` — add deps + `test` script (modify).
- `vitest.config.ts` — Vitest config (create).
- `src/test/setup.ts` — Testing Library setup (create).
- `src/lib/vegaLiteToRecharts.ts` — pure spec→descriptor adapter (create).
- `src/lib/vegaLiteToRecharts.test.ts` — adapter tests (create).
- `src/components/ChartView.tsx` — renders a descriptor with Recharts (create).
- `src/components/ChartView.test.tsx` — smoke test (create).
- `src/theme/theme.css` — design tokens for both themes (create).
- `src/theme/useTheme.ts` — theme state hook (create).
- `src/theme/useTheme.test.ts` — persistence test (create).
- `src/components/ThemeToggle.tsx` — toggle button (create).
- `src/components/Navbar.tsx` — top nav + brand + toggle (create).
- `src/pages/Ask.tsx` — the existing App body, moved (create).
- `src/pages/Dashboard.tsx`, `src/pages/Data.tsx` — placeholders (create).
- `src/App.tsx` — becomes the router shell (modify).
- `src/main.tsx` — wrap in `BrowserRouter` (modify).

---

## Task 1: Test runner + Vega-Lite→Recharts adapter

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/lib/vegaLiteToRecharts.ts`
- Test: `frontend/src/lib/vegaLiteToRecharts.test.ts`

**Interfaces:**
- Produces:
  - `type ChartDescriptor = { kind: "bar" | "line"; categoryKey: string; valueKey: string; title?: string; data: Array<Record<string, string | number | null>> }`
  - `function vegaLiteToRecharts(spec: Record<string, unknown> | null | undefined, rows: Array<Record<string, string | number | null>>): ChartDescriptor | null`
- Behavior derived from [chart_planner.py](../../../backend/app/analytics/chart_planner.py): a `line` spec has `x` = category (ordinal) and `y` = value (quantitative); a `bar` spec is horizontal, so `y` = category (nominal) and `x` = value (quantitative). `mark` may be a string or `{ type }`. Returns `null` when spec is missing, mark is unsupported, or x/y fields are absent.

- [ ] **Step 1: Add dependencies and test script**

Edit `frontend/package.json` to add the `test` script and the new deps:

```json
{
  "scripts": {
    "dev": "vite --host localhost",
    "build": "vite build",
    "preview": "vite preview --host localhost",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "lucide-react": "^0.468.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.1.0",
    "recharts": "^2.15.0",
    "typescript": "^5.7.0",
    "vite": "^6.0.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "jsdom": "^25.0.1",
    "vitest": "^2.1.8"
  }
}
```

- [ ] **Step 2: Install**

Run (from `frontend/`): `npm install`
Expected: completes; `node_modules/.bin/vitest` exists.

- [ ] **Step 3: Create Vitest config**

Create `frontend/vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"]
  }
});
```

- [ ] **Step 4: Create test setup**

Create `frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom";
```

- [ ] **Step 5: Write the failing adapter tests**

Create `frontend/src/lib/vegaLiteToRecharts.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { vegaLiteToRecharts } from "./vegaLiteToRecharts";

const lineSpec = {
  mark: "line",
  title: "Accidents per year",
  encoding: {
    x: { field: "year", type: "ordinal" },
    y: { field: "accidents", type: "quantitative" }
  }
};

const barSpec = {
  mark: "bar",
  encoding: {
    x: { field: "accidents", type: "quantitative" },
    y: { field: "phase", type: "nominal", sort: "-x" }
  }
};

const rows = [
  { year: 2016, phase: "Approach", accidents: 120 },
  { year: 2017, phase: "Landing", accidents: 90 }
];

describe("vegaLiteToRecharts", () => {
  it("maps a line spec: category=x, value=y", () => {
    const d = vegaLiteToRecharts(lineSpec, rows);
    expect(d).toEqual({
      kind: "line",
      categoryKey: "year",
      valueKey: "accidents",
      title: "Accidents per year",
      data: rows
    });
  });

  it("maps a horizontal bar spec: category=y, value=x", () => {
    const d = vegaLiteToRecharts(barSpec, rows);
    expect(d).toMatchObject({ kind: "bar", categoryKey: "phase", valueKey: "accidents" });
  });

  it("accepts an object mark { type }", () => {
    const d = vegaLiteToRecharts({ ...lineSpec, mark: { type: "line" } }, rows);
    expect(d?.kind).toBe("line");
  });

  it("returns null for missing spec", () => {
    expect(vegaLiteToRecharts(null, rows)).toBeNull();
    expect(vegaLiteToRecharts(undefined, rows)).toBeNull();
  });

  it("returns null for unsupported mark", () => {
    expect(vegaLiteToRecharts({ mark: "rect", encoding: barSpec.encoding }, rows)).toBeNull();
  });

  it("returns null when x or y field is absent", () => {
    expect(vegaLiteToRecharts({ mark: "bar", encoding: { x: {}, y: {} } }, rows)).toBeNull();
  });
});
```

- [ ] **Step 6: Run tests to verify they fail**

Run (from `frontend/`): `npm test`
Expected: FAIL — `vegaLiteToRecharts` cannot be imported (module missing).

- [ ] **Step 7: Implement the adapter**

Create `frontend/src/lib/vegaLiteToRecharts.ts`:

```ts
export type ChartRow = Record<string, string | number | null>;

export type ChartDescriptor = {
  kind: "bar" | "line";
  categoryKey: string;
  valueKey: string;
  title?: string;
  data: ChartRow[];
};

function markType(mark: unknown): string | null {
  if (typeof mark === "string") return mark;
  if (mark && typeof mark === "object" && "type" in mark) {
    const t = (mark as { type?: unknown }).type;
    return typeof t === "string" ? t : null;
  }
  return null;
}

function field(channel: unknown): string | null {
  if (channel && typeof channel === "object" && "field" in channel) {
    const f = (channel as { field?: unknown }).field;
    return typeof f === "string" ? f : null;
  }
  return null;
}

export function vegaLiteToRecharts(
  spec: Record<string, unknown> | null | undefined,
  rows: ChartRow[]
): ChartDescriptor | null {
  if (!spec) return null;

  const mark = markType(spec.mark);
  if (mark !== "bar" && mark !== "line") return null;

  const encoding = spec.encoding as Record<string, unknown> | undefined;
  if (!encoding) return null;

  const xField = field(encoding.x);
  const yField = field(encoding.y);
  if (!xField || !yField) return null;

  // Line: x is the category axis, y the value. Bar specs from the backend are
  // horizontal (x = quantitative value, y = nominal category), so the roles flip.
  const categoryKey = mark === "line" ? xField : yField;
  const valueKey = mark === "line" ? yField : xField;

  const title = typeof spec.title === "string" ? spec.title : undefined;

  return { kind: mark, categoryKey, valueKey, title, data: rows };
}
```

- [ ] **Step 8: Run tests to verify they pass**

Run (from `frontend/`): `npm test`
Expected: PASS — all `vegaLiteToRecharts` tests green.

- [ ] **Step 9: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/src/test/setup.ts frontend/src/lib/vegaLiteToRecharts.ts frontend/src/lib/vegaLiteToRecharts.test.ts
git commit -m "feat(frontend): add test runner and Vega-Lite to Recharts adapter"
```

---

## Task 2: ChartView component

**Files:**
- Create: `frontend/src/components/ChartView.tsx`
- Test: `frontend/src/components/ChartView.test.tsx`

**Interfaces:**
- Consumes: `vegaLiteToRecharts`, `ChartDescriptor` from `src/lib/vegaLiteToRecharts`.
- Produces: `function ChartView(props: { spec: Record<string, unknown> | null | undefined; rows: ChartRow[] }): JSX.Element | null` — returns `null` when the adapter yields `null`; otherwise renders a Recharts bar or line chart inside a `ResponsiveContainer`. Bars/lines use CSS var `--chart-series` (falls back to teal).

- [ ] **Step 1: Write the failing smoke test**

Create `frontend/src/components/ChartView.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { ChartView } from "./ChartView";

const rows = [
  { phase: "Approach", accidents: 120 },
  { phase: "Landing", accidents: 90 }
];
const barSpec = {
  mark: "bar",
  title: "By phase",
  encoding: {
    x: { field: "accidents", type: "quantitative" },
    y: { field: "phase", type: "nominal" }
  }
};

describe("ChartView", () => {
  it("renders the chart title for a valid spec", () => {
    const { getByText } = render(<ChartView spec={barSpec} rows={rows} />);
    expect(getByText("By phase")).toBeInTheDocument();
  });

  it("renders nothing for an unsupported spec", () => {
    const { container } = render(<ChartView spec={{ mark: "rect" }} rows={rows} />);
    expect(container.firstChild).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `npm test -- ChartView`
Expected: FAIL — `ChartView` module missing.

- [ ] **Step 3: Implement ChartView**

Create `frontend/src/components/ChartView.tsx`:

```tsx
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { vegaLiteToRecharts, type ChartRow } from "../lib/vegaLiteToRecharts";

const SERIES = "var(--chart-series, #1f6f78)";

export function ChartView({
  spec,
  rows
}: {
  spec: Record<string, unknown> | null | undefined;
  rows: ChartRow[];
}) {
  const descriptor = vegaLiteToRecharts(spec, rows);
  if (!descriptor) return null;

  const { kind, categoryKey, valueKey, title, data } = descriptor;

  return (
    <figure className="chart-view">
      {title && <figcaption className="chart-title">{title}</figcaption>}
      <div className="chart-host">
        <ResponsiveContainer width="100%" height={340}>
          {kind === "line" ? (
            <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--rule, #e3e8eb)" />
              <XAxis dataKey={categoryKey} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey={valueKey} stroke={SERIES} strokeWidth={2} dot={false} />
            </LineChart>
          ) : (
            <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--rule, #e3e8eb)" />
              <XAxis type="number" dataKey={valueKey} />
              <YAxis type="category" dataKey={categoryKey} width={140} />
              <Tooltip />
              <Bar dataKey={valueKey} fill={SERIES} radius={[0, 2, 2, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </figure>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run (from `frontend/`): `npm test -- ChartView`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ChartView.tsx frontend/src/components/ChartView.test.tsx
git commit -m "feat(frontend): add Recharts ChartView component"
```

---

## Task 3: Theme tokens + useTheme hook

**Files:**
- Create: `frontend/src/theme/theme.css`
- Create: `frontend/src/theme/useTheme.ts`
- Test: `frontend/src/theme/useTheme.test.ts`

**Interfaces:**
- Produces:
  - `type Theme = "light" | "dark"`
  - `function useTheme(): { theme: Theme; toggle: () => void; setTheme: (t: Theme) => void }` — on mount reads `localStorage["blackbox-theme"]`, else `prefers-color-scheme`, defaults `"light"`; writes `data-theme` on `document.documentElement` and persists to `localStorage` on change.

- [ ] **Step 1: Create theme tokens CSS**

Create `frontend/src/theme/theme.css`:

```css
:root,
[data-theme="light"] {
  --bg: #f5f7f8;
  --surface: #ffffff;
  --text: #172026;
  --muted: #60717d;
  --rule: #e3e8eb;
  --primary: #1f6f78;
  --danger: #b3402f;
  --chart-series: #1f6f78;
  --serif: Georgia, "Times New Roman", ui-serif, serif;
  --sans: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}

[data-theme="dark"] {
  --bg: #0e1620;
  --surface: #16212e;
  --text: #d6e2ec;
  --muted: #7d93a6;
  --rule: #22303f;
  --primary: #5cc8c2;
  --danger: #e6a23c;
  --chart-series: #5cc8c2;
}

html { background: var(--bg); color: var(--text); }

.tabular { font-variant-numeric: tabular-nums; }
```

- [ ] **Step 2: Write the failing hook test**

Create `frontend/src/theme/useTheme.test.ts`:

```ts
import { describe, it, expect, beforeEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useTheme } from "./useTheme";

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

describe("useTheme", () => {
  it("defaults to light and sets data-theme on the html element", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("toggles and persists to localStorage", () => {
    const { result } = renderHook(() => useTheme());
    act(() => result.current.toggle());
    expect(result.current.theme).toBe("dark");
    expect(window.localStorage.getItem("blackbox-theme")).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("reads a persisted value on mount", () => {
    window.localStorage.setItem("blackbox-theme", "dark");
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("dark");
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run (from `frontend/`): `npm test -- useTheme`
Expected: FAIL — `useTheme` module missing.

- [ ] **Step 4: Implement useTheme**

Create `frontend/src/theme/useTheme.ts`:

```ts
import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark";

const STORAGE_KEY = "blackbox-theme";

function initialTheme(): Theme {
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) return "dark";
  return "light";
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(initialTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    window.localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => setThemeState(next), []);
  const toggle = useCallback(
    () => setThemeState((current) => (current === "light" ? "dark" : "light")),
    []
  );

  return { theme, toggle, setTheme };
}
```

- [ ] **Step 5: Run test to verify it passes**

Run (from `frontend/`): `npm test -- useTheme`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/theme/theme.css frontend/src/theme/useTheme.ts frontend/src/theme/useTheme.test.ts
git commit -m "feat(frontend): add theme tokens and useTheme hook"
```

---

## Task 4: ThemeToggle + Navbar

**Files:**
- Create: `frontend/src/components/ThemeToggle.tsx`
- Create: `frontend/src/components/Navbar.tsx`
- Test: `frontend/src/components/Navbar.test.tsx`

**Interfaces:**
- Consumes: `useTheme` from `src/theme/useTheme`; `NavLink` from `react-router-dom`.
- Produces: `function Navbar(): JSX.Element` with brand, three `NavLink`s (`/` Dashboard, `/ask` Ask, `/data` Data), and a `ThemeToggle`. `function ThemeToggle(): JSX.Element` — a button showing a sun/moon icon that calls `toggle()`.

- [ ] **Step 1: Write the failing Navbar test**

Create `frontend/src/components/Navbar.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Navbar } from "./Navbar";

describe("Navbar", () => {
  it("renders the three section links and a theme toggle", () => {
    const { getByRole } = render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    expect(getByRole("link", { name: /dashboard/i })).toBeInTheDocument();
    expect(getByRole("link", { name: /ask/i })).toBeInTheDocument();
    expect(getByRole("link", { name: /data/i })).toBeInTheDocument();
    expect(getByRole("button", { name: /theme/i })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `npm test -- Navbar`
Expected: FAIL — `Navbar` module missing.

- [ ] **Step 3: Implement ThemeToggle**

Create `frontend/src/components/ThemeToggle.tsx`:

```tsx
import { Moon, Sun } from "lucide-react";
import { useTheme } from "../theme/useTheme";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      type="button"
      className="theme-toggle"
      aria-label={`Switch theme (currently ${theme})`}
      onClick={toggle}
    >
      {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
    </button>
  );
}
```

- [ ] **Step 4: Implement Navbar**

Create `frontend/src/components/Navbar.tsx`:

```tsx
import { Plane } from "lucide-react";
import { NavLink } from "react-router-dom";
import { ThemeToggle } from "./ThemeToggle";

export function Navbar() {
  return (
    <header className="navbar">
      <div className="brand">
        <Plane size={20} />
        <span className="brand-name">Black Box</span>
      </div>
      <nav className="nav-links">
        <NavLink to="/" end>Dashboard</NavLink>
        <NavLink to="/ask">Ask</NavLink>
        <NavLink to="/data">Data</NavLink>
      </nav>
      <ThemeToggle />
    </header>
  );
}
```

- [ ] **Step 5: Run test to verify it passes**

Run (from `frontend/`): `npm test -- Navbar`
Expected: PASS.

> Note: `useTheme` mounted twice (toggle + any other consumer) each sync to the
> same `localStorage`/attribute, so there is no shared-context requirement for
> this plan. A future task may lift it to context if cross-component reads diverge.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ThemeToggle.tsx frontend/src/components/Navbar.tsx frontend/src/components/Navbar.test.tsx
git commit -m "feat(frontend): add navbar and theme toggle"
```

---

## Task 5: Router shell + page scaffolds

**Files:**
- Create: `frontend/src/pages/Ask.tsx`
- Create: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/pages/Data.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: `Navbar`; `Routes`, `Route`, `BrowserRouter` from `react-router-dom`; theme CSS.
- Produces: `App` renders `<Navbar/>` + a `<Routes>` mapping `/`→`Dashboard`, `/ask`→`Ask`, `/data`→`Data`. `main.tsx` wraps `<App/>` in `<BrowserRouter>`. `pages/Ask.tsx` contains the current ask-and-answer flow moved verbatim from the old `App.tsx`.

- [ ] **Step 1: Move the existing Ask flow into `pages/Ask.tsx`**

Create `frontend/src/pages/Ask.tsx` with the current body of `App.tsx` (the session id, provider/model/apiKey/question state, `ask()`, `clearKey()`, and the JSX from `<div className="workspace">` down — i.e. everything except the `<header className="topbar">`, which the Navbar replaces). Rename the exported component to `Ask`:

```tsx
import { useMemo, useState } from "react";
import { AskPanel } from "../components/AskPanel";
import { ProviderKeyPanel, modelOptions } from "../components/ProviderKeyPanel";
import { ResultPanels } from "../components/ResultPanels";
import type { AskResponse, Provider } from "../types";

const sessionKey = "blackbox-session-id";
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

function getSessionId() {
  const existing = window.localStorage.getItem(sessionKey);
  if (existing) return existing;
  const created = crypto.randomUUID();
  window.localStorage.setItem(sessionKey, created);
  return created;
}

export function Ask() {
  const sessionId = useMemo(getSessionId, []);
  const [provider, setProvider] = useState<Provider>("openai");
  const [model, setModel] = useState(modelOptions.openai[0]);
  const [apiKey, setApiKey] = useState("");
  const [question, setQuestion] = useState(
    "Which phases of flight have the highest fatal accident counts, and show it as a chart?"
  );
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask() {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const res = await fetch(`${API_BASE}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Session-ID": sessionId },
        body: JSON.stringify({
          question,
          provider,
          model,
          api_key: apiKey || null,
          chart_preference: "auto",
          session_id: sessionId
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request failed");
      setResponse(data);
      setApiKey("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function clearKey() {
    await fetch(`${API_BASE}/api/keys/clear`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Session-ID": sessionId },
      body: JSON.stringify({ provider, session_id: sessionId })
    });
    setApiKey("");
  }

  return (
    <div className="workspace">
      <section className="main-column">
        <details className="provider-menu">
          <summary>Model Key</summary>
          <ProviderKeyPanel
            provider={provider}
            model={model}
            apiKey={apiKey}
            onProviderChange={(nextProvider) => {
              setProvider(nextProvider);
              setModel(modelOptions[nextProvider][0]);
            }}
            onModelChange={setModel}
            onApiKeyChange={setApiKey}
            onClear={clearKey}
          />
        </details>
        <AskPanel question={question} loading={loading} onQuestionChange={setQuestion} onSubmit={ask} />
        {error && <div className="error">{error}</div>}
        <ResultPanels response={response} />
      </section>
    </div>
  );
}
```

- [ ] **Step 2: Create placeholder pages**

Create `frontend/src/pages/Dashboard.tsx`:

```tsx
export function Dashboard() {
  return (
    <div className="workspace">
      <section className="main-column">
        <h1>Dashboard</h1>
        <p className="subtitle">Analytics gallery coming next.</p>
      </section>
    </div>
  );
}
```

Create `frontend/src/pages/Data.tsx`:

```tsx
export function Data() {
  return (
    <div className="workspace">
      <section className="main-column">
        <h1>Data</h1>
        <p className="subtitle">Dataset provenance card coming next.</p>
      </section>
    </div>
  );
}
```

- [ ] **Step 3: Write the failing router test**

Create `frontend/src/App.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";

describe("App routing", () => {
  it("renders the Dashboard at /", () => {
    const { getByText } = render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );
    expect(getByText("Dashboard")).toBeInTheDocument();
  });

  it("renders the Ask page at /ask", () => {
    const { getByPlaceholderText } = render(
      <MemoryRouter initialEntries={["/ask"]}>
        <App />
      </MemoryRouter>
    );
    expect(getByPlaceholderText(/ask about the loaded ntsb/i)).toBeInTheDocument();
  });
});
```

Note: `App.test.tsx` provides its own router, so `App` must NOT include `BrowserRouter` itself — the router lives in `main.tsx` (Step 5).

- [ ] **Step 4: Rewrite `App.tsx` as the router shell**

Replace `frontend/src/App.tsx` entirely:

```tsx
import { Route, Routes } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { Dashboard } from "./pages/Dashboard";
import { Ask } from "./pages/Ask";
import { Data } from "./pages/Data";
import "./theme/theme.css";
import "./styles.css";

export default function App() {
  return (
    <main>
      <Navbar />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/ask" element={<Ask />} />
        <Route path="/data" element={<Data />} />
      </Routes>
    </main>
  );
}
```

- [ ] **Step 5: Wrap the app in BrowserRouter**

Replace `frontend/src/main.tsx`:

```tsx
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Root element not found.");
}

createRoot(root).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);
```

- [ ] **Step 6: Run the router tests to verify they pass**

Run (from `frontend/`): `npm test -- App`
Expected: PASS — both routing tests green.

- [ ] **Step 7: Run the full suite and a type/build check**

Run (from `frontend/`): `npm test`
Expected: PASS — all suites (adapter, ChartView, useTheme, Navbar, App).

Run (from `frontend/`): `npm run build`
Expected: build succeeds with no TypeScript errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/Ask.tsx frontend/src/pages/Dashboard.tsx frontend/src/pages/Data.tsx frontend/src/App.tsx frontend/src/main.tsx frontend/src/App.test.tsx
git commit -m "feat(frontend): add router shell with Dashboard/Ask/Data pages"
```

---

## Self-Review Notes

- **Spec coverage (foundation portion):** theme tokens + dark toggle (Tasks 3–4), CSS-variable theming with `data-theme` (Task 3), React Router 3-page shell (Task 5), Recharts + `vegaLiteToRecharts` adapter (Tasks 1–2), navbar with toggle (Task 4). Dashboard/Ask-redesign/Data/News content is intentionally deferred to Plans 2–5.
- **Navbar/Ask use of `ResultPanels`/`AskPanel`/`ProviderKeyPanel`** is unchanged here — the Ask redesign (tabs, ChartView, limitations-always-visible) is Plan 3; this plan only relocates the existing flow so routing works without regression.
- **Placeholder scan:** none — every code step contains full content.
- **Type consistency:** `ChartDescriptor`/`vegaLiteToRecharts` signatures match between Tasks 1 and 2; `useTheme` return shape matches between Tasks 3 and 4.
