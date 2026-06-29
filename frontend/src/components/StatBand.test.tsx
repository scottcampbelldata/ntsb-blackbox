import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { StatBand } from "./StatBand";

describe("StatBand", () => {
  it("formats counts and derives the fatal rate", () => {
    const { getByText } = render(
      <StatBand
        kpis={{ accident_count: 7462, fatal_count: 1122, min_year: 2016, max_year: 2024, distinct_makes: 480 }}
      />
    );
    expect(getByText("7,462")).toBeInTheDocument();
    expect(getByText("1,122")).toBeInTheDocument();
    expect(getByText("2016-2024")).toBeInTheDocument();
    expect(getByText("15.0% of accidents")).toBeInTheDocument(); // 1122 / 7462
  });

  it("shows N/A when the year range is missing", () => {
    const { getByText } = render(
      <StatBand
        kpis={{ accident_count: 10, fatal_count: 0, min_year: null, max_year: null, distinct_makes: 3 }}
      />
    );
    expect(getByText("N/A")).toBeInTheDocument();
  });
});
