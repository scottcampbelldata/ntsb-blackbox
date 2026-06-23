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
