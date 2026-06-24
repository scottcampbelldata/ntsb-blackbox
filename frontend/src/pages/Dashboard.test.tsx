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
