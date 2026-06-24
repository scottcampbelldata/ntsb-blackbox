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
    expect(getByText("2016-2023")).toBeInTheDocument();
    expect(getByText("340")).toBeInTheDocument();
  });

  it("shows N/A fallback when min_year is null", () => {
    const { getByText } = render(<KpiStrip kpis={{ ...kpis, min_year: null }} />);
    expect(getByText("N/A")).toBeInTheDocument();
  });
});
