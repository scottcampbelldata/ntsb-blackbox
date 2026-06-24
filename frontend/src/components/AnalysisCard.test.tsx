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
