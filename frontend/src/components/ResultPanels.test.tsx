import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@testing-library/react";
import { ResultPanels } from "./ResultPanels";
import type { AskResponse } from "../types";

vi.mock("../lib/api", () => ({ fetchContext: vi.fn() }));

import { fetchContext } from "../lib/api";

beforeEach(() => vi.mocked(fetchContext).mockReset());

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
  limitations: ["Years 2020-2021 are absent."],
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
    expect(getByText("Years 2020-2021 are absent.")).toBeInTheDocument();
    expect(getByText("BOTH")).toBeInTheDocument();
  });

  it("shows the SQL tab content by default and switches to Citations", () => {
    const { getByRole, getByText } = render(<ResultPanels response={response} />);
    expect(getByText(/SELECT phase/)).toBeInTheDocument();
    fireEvent.click(getByRole("tab", { name: /Citations/ }));
    expect(getByText("ABC123")).toBeInTheDocument();
  });

  it("auto-loads news coverage and surfaces it near the top", async () => {
    vi.mocked(fetchContext).mockResolvedValue({
      query: "Cessna aviation accident Reno",
      source: "gdelt",
      articles: [{ title: "Crash makes headlines", url: "https://news.x/1", domain: "news.x", date: "20190101" }],
      search_url: "https://news.google.com/search?q=x"
    });
    const withId: AskResponse = {
      ...response,
      citations: [{ ...response.citations[0], make: "Cessna", city: "Reno", event_year: 2017 }]
    };
    const { getByText } = render(<ResultPanels response={withId} />);
    await waitFor(() => expect(getByText("Crash makes headlines")).toBeInTheDocument());
    expect(fetchContext).toHaveBeenCalledTimes(1);
  });
});
