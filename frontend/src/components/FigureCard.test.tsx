import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { FigureCard } from "./FigureCard";
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

const rateAnalysis: AnalysisResult = {
  key: "fatal_rate_by_phase",
  label: "Fatality rate by phase of flight",
  sql: "SELECT broad_phaseof_flight, ... FROM accidents",
  columns: ["phase", "accidents", "fatal", "fatal_rate_pct"],
  rows: [{ phase: "Maneuvering", accidents: 862, fatal: 290, fatal_rate_pct: 33.6 }],
  chart_spec: { mark: "bar", encoding: { x: { field: "fatal_rate_pct" }, y: { field: "phase" } } },
  note: "The inversion that matters."
};

describe("FigureCard", () => {
  it("shows the title, note, and the SQL behind it", () => {
    const { getByRole, getByText } = render(<FigureCard analysis={rateAnalysis} />);
    expect(getByRole("heading", { name: rateAnalysis.label })).toBeInTheDocument();
    expect(getByText("The inversion that matters.")).toBeInTheDocument();
    expect(getByText("View SQL")).toBeInTheDocument();
    expect(getByText(/SELECT broad_phaseof_flight/)).toBeInTheDocument();
  });

  it("labels a rate figure by what its axis measures", () => {
    const { getByText } = render(<FigureCard analysis={rateAnalysis} />);
    expect(getByText("Share fatal · %")).toBeInTheDocument();
  });

  it("labels a plain count figure as a count", () => {
    const count: AnalysisResult = {
      ...rateAnalysis,
      key: "top_makes",
      label: "Top aircraft makes",
      columns: ["make", "accidents"],
      note: null
    };
    const { getByText } = render(<FigureCard analysis={count} />);
    expect(getByText("Count")).toBeInTheDocument();
  });
});
