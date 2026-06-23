import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render } from "@testing-library/react";
import { ChartView } from "./ChartView";

vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 800, height: 340 }}>{children}</div>
    )
  };
});

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
