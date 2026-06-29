import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { AnswerArticle } from "./AnswerArticle";
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

vi.mock("../lib/api", () => ({
  fetchContext: vi.fn().mockResolvedValue({ query: "", source: "fallback", articles: [], search_url: "" })
}));

const response: AskResponse = {
  session_id: "s",
  question: "q",
  route: { route: "analytics", sql_triggers: [], retrieval_triggers: [], chart_triggers: [] },
  answer: "Maneuvering has the highest fatality rate.",
  sql: "SELECT 1",
  table: { columns: ["phase", "fatal"], rows: [{ phase: "Maneuvering", fatal: 290 }] },
  chart_spec: null,
  citations: [{ ntsb_no: "WPR19FA124", score: 0.8, matched_passage: "…", probable_cause: "loss of control" }],
  confidence: 0.82,
  limitations: ["Counts depend on report completeness."],
  audit: [{ step: "route", detail: "classified as analytics" }]
};

describe("AnswerArticle", () => {
  it("renders nothing without a response", () => {
    const { container } = render(<AnswerArticle response={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the answer, byline, methodology tabs, and limitations", () => {
    const { getByText, getByRole } = render(<AnswerArticle response={response} />);
    expect(getByText("Maneuvering has the highest fatality rate.")).toBeInTheDocument();
    expect(getByText("analytics")).toBeInTheDocument();
    expect(getByText("82% confidence")).toBeInTheDocument();
    expect(getByRole("tab", { name: "SQL" })).toBeInTheDocument();
    expect(getByText("Counts depend on report completeness.")).toBeInTheDocument();
  });
});
