# Redesign Plan 3 — Ask Page Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the Ask page's result presentation into a clean, Editorial-themed layout — answer + route badge + confidence up top, a real Recharts chart, a tab bar for SQL / Table / Citations / Audit, and an always-visible Limitations section — and unify the Ask flow onto the shared `lib/api.ts` client.

**Architecture:** The verbose result artifacts move into a small accessible `Tabs` component; the hand-rolled CSS/SVG charts in `ResultPanels` are replaced by Plan 1's `ChartView` (rendering the backend's `chart_spec`). `pages/Ask.tsx`'s bespoke fetch/`API_BASE` is replaced by `ask()`/`clearKey()` helpers in `lib/api.ts`, removing the duplication the earlier plans deferred.

**Tech Stack:** React 19, Recharts, Vitest + Testing Library. Builds on Plan 1 (`ChartView`) and Plan 2 (`lib/api.ts`).

## Global Constraints

- Result layout: (1) answer text + route badge (`route.route` upper-cased) + confidence (`Math.round(confidence*100)%`) at the top; (2) `ChartView` when `chart_spec` and `table` are present; (3) a tab bar for SQL / Table / Citations / Audit (include only tabs that have content; Audit always present); (4) **Limitations always visible** below the tabs (never inside a tab).
- Charts render via `ChartView` (`spec={response.chart_spec}`, `rows={response.table.rows}`) — no hand-rolled chart code remains in `ResultPanels`.
- Citations show the NTSB record link (`report_url`) when present; the "related coverage" expander is Plan 5 (do not add it here).
- All colors come from theme tokens (`var(--…)`); no hardcoded hex in new CSS.
- `pages/Ask.tsx` uses `lib/api.ts` for the API base and the ask/clear calls — no local `API_BASE` or inline `fetch` remains.
- React ^19, Vite ^6, TS ^5.7. Run frontend commands from `frontend/`.

---

## File Structure

Frontend (`frontend/src/`):
- `lib/api.ts` — add `AskRequestParams`, `ask()`, `clearKey()`; re-use `API_BASE` (modify).
- `pages/Ask.tsx` — use `ask()`/`clearKey()` from `lib/api.ts` (modify).
- `components/Tabs.tsx` + `Tabs.test.tsx` — accessible tab component (create).
- `components/ResultPanels.tsx` — rewrite into the new layout (modify) + `ResultPanels.test.tsx` (create).
- `styles.css` — Ask result / tabs / badge styles (modify).

---

## Task 1: Extend the API client and unify Ask

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/pages/Ask.tsx`
- Test: `frontend/src/lib/api.test.ts`

**Interfaces:**
- Consumes: `AskResponse`, `Provider` from `../types`.
- Produces (`lib/api.ts`):
  - `type AskRequestParams = { question: string; provider: Provider; model: string; apiKey: string | null; sessionId: string }`
  - `async function ask(params: AskRequestParams): Promise<AskResponse>`
  - `async function clearKey(params: { provider: Provider; sessionId: string }): Promise<void>`

- [ ] **Step 1: Write the failing api test**

Create `frontend/src/lib/api.test.ts`:

```ts
import { describe, it, expect, vi, afterEach } from "vitest";
import { ask } from "./api";

afterEach(() => vi.restoreAllMocks());

describe("ask", () => {
  it("POSTs the question and returns the parsed response", async () => {
    const fake = { answer: "ok", route: { route: "sql" }, citations: [], audit: [], limitations: [] };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => fake });
    vi.stubGlobal("fetch", fetchMock);

    const result = await ask({
      question: "how many accidents",
      provider: "openai",
      model: "gpt-4o",
      apiKey: null,
      sessionId: "s1"
    });

    expect(result).toEqual(fake);
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/api\/ask$/);
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body);
    expect(body.question).toBe("how many accidents");
    expect(body.session_id).toBe("s1");
  });

  it("throws with the backend detail on error", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, json: async () => ({ detail: "bad key" }) });
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      ask({ question: "q", provider: "openai", model: "m", apiKey: "k", sessionId: "s" })
    ).rejects.toThrow("bad key");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `npm test -- api`
Expected: FAIL — `ask` is not exported from `./api`.

- [ ] **Step 3: Add ask/clearKey to the API client**

Append to `frontend/src/lib/api.ts` (keep existing exports; add the `Provider`/`AskResponse` import at the top alongside the existing `ChartRow` import):

```ts
import type { AskResponse, Provider } from "../types";

export type AskRequestParams = {
  question: string;
  provider: Provider;
  model: string;
  apiKey: string | null;
  sessionId: string;
};

export async function ask(params: AskRequestParams): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Session-ID": params.sessionId },
    body: JSON.stringify({
      question: params.question,
      provider: params.provider,
      model: params.model,
      api_key: params.apiKey,
      chart_preference: "auto",
      session_id: params.sessionId
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Request failed");
  return data as AskResponse;
}

export async function clearKey(params: { provider: Provider; sessionId: string }): Promise<void> {
  await fetch(`${API_BASE}/api/keys/clear`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Session-ID": params.sessionId },
    body: JSON.stringify({ provider: params.provider, session_id: params.sessionId })
  });
}
```

- [ ] **Step 4: Refactor `pages/Ask.tsx` to use them**

In `frontend/src/pages/Ask.tsx`: remove the local `API_BASE` constant and its comment, remove the inline `fetch` bodies, and import the helpers. Replace the `ask`/`clearKey` functions' bodies:

- Add import: `import { ask as askApi, clearKey as clearKeyApi } from "../lib/api";`
- Delete the line `const API_BASE = import.meta.env.VITE_API_BASE ?? "";` and the two comment lines above it.
- Replace the component's `async function ask() {…}` body with:

```tsx
  async function ask() {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const data = await askApi({ question, provider, model, apiKey: apiKey || null, sessionId });
      setResponse(data);
      setApiKey("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }
```

- Replace `async function clearKey() {…}` body with:

```tsx
  async function clearKey() {
    await clearKeyApi({ provider, sessionId });
    setApiKey("");
  }
```

- [ ] **Step 5: Run tests + build to verify**

Run (from `frontend/`): `npm test -- api`
Expected: PASS.

Run (from `frontend/`): `npm run build`
Expected: build succeeds, no TS errors (confirms `Ask.tsx` still type-checks after the refactor).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/lib/api.test.ts frontend/src/pages/Ask.tsx
git commit -m "refactor(frontend): move Ask fetch logic into shared api client"
```

---

## Task 2: Tabs component

**Files:**
- Create: `frontend/src/components/Tabs.tsx`
- Test: `frontend/src/components/Tabs.test.tsx`

**Interfaces:**
- Produces: `type TabItem = { id: string; label: string; content: React.ReactNode }`; `function Tabs(props: { tabs: TabItem[] }): JSX.Element | null` — renders a `role="tablist"` of buttons and the selected tab's content; first tab selected by default; clicking a tab shows its content. Returns `null` for an empty `tabs` array.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/Tabs.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { Tabs } from "./Tabs";

const tabs = [
  { id: "sql", label: "SQL", content: <p>the sql</p> },
  { id: "table", label: "Table", content: <p>the table</p> }
];

describe("Tabs", () => {
  it("shows the first tab by default and switches on click", () => {
    const { getByRole, getByText, queryByText } = render(<Tabs tabs={tabs} />);
    expect(getByText("the sql")).toBeInTheDocument();
    expect(queryByText("the table")).toBeNull();
    fireEvent.click(getByRole("tab", { name: "Table" }));
    expect(getByText("the table")).toBeInTheDocument();
    expect(queryByText("the sql")).toBeNull();
  });

  it("renders nothing when there are no tabs", () => {
    const { container } = render(<Tabs tabs={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `npm test -- Tabs`
Expected: FAIL — `Tabs` module missing.

- [ ] **Step 3: Implement Tabs**

Create `frontend/src/components/Tabs.tsx`:

```tsx
import { useState } from "react";

export type TabItem = { id: string; label: string; content: React.ReactNode };

export function Tabs({ tabs }: { tabs: TabItem[] }) {
  const [active, setActive] = useState(0);
  if (tabs.length === 0) return null;
  const current = tabs[Math.min(active, tabs.length - 1)];

  return (
    <div className="tabs">
      <div className="tablist" role="tablist">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={index === active}
            className={`tab${index === active ? " tab-active" : ""}`}
            onClick={() => setActive(index)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tab-panel" role="tabpanel">
        {current.content}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run (from `frontend/`): `npm test -- Tabs`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/Tabs.tsx frontend/src/components/Tabs.test.tsx
git commit -m "feat(frontend): add accessible Tabs component"
```

---

## Task 3: Rewrite ResultPanels

**Files:**
- Modify: `frontend/src/components/ResultPanels.tsx`
- Test: `frontend/src/components/ResultPanels.test.tsx`

**Interfaces:**
- Consumes: `ChartView` from `./ChartView`; `Tabs`, `TabItem` from `./Tabs`; `AskResponse` from `../types`.
- Produces: `function ResultPanels(props: { response: AskResponse | null }): JSX.Element | null` — returns `null` when `response` is null; otherwise renders the answer header (answer, route badge, confidence), `ChartView` when `chart_spec` + `table` exist, a `Tabs` of the available artifacts (SQL, Table, Citations, Audit), and an always-visible Limitations section.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/components/ResultPanels.test.tsx`:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { ResultPanels } from "./ResultPanels";
import type { AskResponse } from "../types";

vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 800, height: 340 }}>{children}</div>
    )
  };
});

const response: AskResponse = {
  session_id: "s",
  question: "q",
  route: { route: "both", sql_triggers: [], retrieval_triggers: [], chart_triggers: [] },
  answer: "Approach and landing have the highest fatal counts.",
  sql: "SELECT phase, COUNT(*) FROM accidents GROUP BY phase",
  table: { columns: ["phase", "accidents"], rows: [{ phase: "Approach", accidents: 120 }] },
  chart_spec: { mark: "bar", encoding: { x: { field: "accidents" }, y: { field: "phase" } } },
  citations: [
    { ntsb_no: "ABC123", score: 0.9, matched_passage: "…", probable_cause: "pilot error", report_url: "https://ntsb.gov/ABC123" }
  ],
  confidence: 0.92,
  limitations: ["Years 2020–2021 are absent."],
  audit: [{ step: "route", detail: "routed to both" }]
};

describe("ResultPanels", () => {
  it("returns null with no response", () => {
    const { container } = render(<ResultPanels response={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the answer, confidence, and always-visible limitations", () => {
    const { getByText } = render(<ResultPanels response={response} />);
    expect(getByText(/highest fatal counts/)).toBeInTheDocument();
    expect(getByText(/92%/)).toBeInTheDocument();
    expect(getByText("Years 2020–2021 are absent.")).toBeInTheDocument();
  });

  it("shows the SQL tab content by default and switches to Citations", () => {
    const { getByRole, getByText } = render(<ResultPanels response={response} />);
    expect(getByText(/SELECT phase/)).toBeInTheDocument();
    getByRole("tab", { name: /Citations/ }).click();
    expect(getByText("ABC123")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `npm test -- ResultPanels`
Expected: FAIL — the current `ResultPanels` has no tabs/role="tab", so the assertions fail (or the import of `Tabs` is missing).

- [ ] **Step 3: Rewrite ResultPanels**

Replace `frontend/src/components/ResultPanels.tsx` entirely:

```tsx
import { ChartView } from "./ChartView";
import { Tabs, type TabItem } from "./Tabs";
import type { AskResponse } from "../types";

function AnswerHeader({ response }: { response: AskResponse }) {
  return (
    <section className="answer-header">
      <p className="answer-text">{response.answer}</p>
      <div className="answer-meta">
        <span className="route-badge">{response.route.route.toUpperCase()}</span>
        <span className="confidence tabular">{Math.round(response.confidence * 100)}% confidence</span>
      </div>
    </section>
  );
}

function ResultTable({ table }: { table: NonNullable<AskResponse["table"]> }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>{table.columns.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {table.rows.map((row, i) => (
            <tr key={i}>{table.columns.map((c) => <td key={c}>{String(row[c] ?? "")}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Citations({ citations }: { citations: AskResponse["citations"] }) {
  return (
    <div className="citation-list">
      {citations.map((c) => (
        <article key={c.ntsb_no} className="citation">
          {c.report_url ? (
            <a href={c.report_url} target="_blank" rel="noreferrer">{c.ntsb_no}</a>
          ) : (
            <span className="citation-id">{c.ntsb_no}</span>
          )}
          <p>{c.probable_cause || c.matched_passage}</p>
        </article>
      ))}
    </div>
  );
}

export function ResultPanels({ response }: { response: AskResponse | null }) {
  if (!response) return null;

  const tabs: TabItem[] = [];
  if (response.sql) {
    tabs.push({ id: "sql", label: "SQL", content: <pre>{response.sql}</pre> });
  }
  if (response.table) {
    tabs.push({ id: "table", label: "Table", content: <ResultTable table={response.table} /> });
  }
  if (response.citations.length > 0) {
    tabs.push({
      id: "citations",
      label: `Citations (${response.citations.length})`,
      content: <Citations citations={response.citations} />
    });
  }
  tabs.push({
    id: "audit",
    label: "Audit",
    content: (
      <ol className="audit-list">
        {response.audit.map((e, i) => (
          <li key={`${e.step}-${i}`}>
            <strong>{e.step}</strong>
            <span>{e.detail}</span>
          </li>
        ))}
      </ol>
    )
  });

  return (
    <div className="result">
      <AnswerHeader response={response} />
      {response.chart_spec && response.table && (
        <section className="result-chart">
          <ChartView spec={response.chart_spec} rows={response.table.rows} />
        </section>
      )}
      <Tabs tabs={tabs} />
      {response.limitations.length > 0 && (
        <section className="limitations">
          <h4>Limitations</h4>
          <ul className="limit-list">
            {response.limitations.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </section>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run (from `frontend/`): `npm test -- ResultPanels`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ResultPanels.tsx frontend/src/components/ResultPanels.test.tsx
git commit -m "feat(frontend): redesign Ask result with tabs, chart, and visible limitations"
```

---

## Task 4: Ask result styling + full verification

**Files:**
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Add the Ask result / tabs / badge styles**

Append to `frontend/src/styles.css`:

```css
.result {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.answer-header {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-left: 4px solid var(--primary);
  border-radius: 8px;
  padding: 16px;
}

.answer-text {
  font-size: 17px;
  line-height: 1.55;
  margin: 0;
}

.answer-meta {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.route-badge {
  background: var(--primary);
  border-radius: 999px;
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 4px 10px;
}

.confidence {
  color: var(--muted);
  font-size: 13px;
  font-weight: 700;
  padding: 4px 0;
}

.result-chart,
.tabs,
.limitations {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-radius: 8px;
  padding: 16px;
}

.tablist {
  border-bottom: 1px solid var(--rule);
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
}

.tab {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--muted);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  padding: 8px 12px;
}

.tab-active {
  border-bottom-color: var(--primary);
  color: var(--primary);
}

.limitations h4 {
  font-family: var(--serif);
  margin: 0 0 8px;
}
```

- [ ] **Step 2: Run the full suite**

Run (from `frontend/`): `npm test`
Expected: PASS — all suites including `api`, `Tabs`, `ResultPanels`, plus the Plan 1/2 suites.

- [ ] **Step 3: Build**

Run (from `frontend/`): `npm run build`
Expected: build succeeds, no TS errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/styles.css
git commit -m "style(frontend): theme the redesigned Ask result and tabs"
```

---

## Self-Review Notes

- **Spec coverage:** answer header + route badge + confidence (Task 3 `AnswerHeader`), chart via `ChartView` (Task 3), tab bar SQL/Table/Citations/Audit (Tasks 2–3), limitations always visible outside tabs (Task 3), citations with NTSB links (Task 3), Ask unified onto `lib/api.ts` (Task 1), theme-token styling (Task 4).
- **DRY win:** the hand-rolled `BarChart`/`LineChart` SVG code is deleted from `ResultPanels` in favor of `ChartView` (single chart-rendering path across Dashboard and Ask).
- **Placeholder scan:** none — every code step is complete.
- **Type consistency:** `ask()`/`clearKey()` params (Task 1) match `pages/Ask.tsx`'s call sites; `TabItem` (Task 2) is consumed unchanged by `ResultPanels` (Task 3); `AskResponse` is the existing type from `../types`, unchanged.
- **Deferred to Plan 5:** the citation "related coverage" expander (GDELT) — citations here only carry the NTSB link.
```
