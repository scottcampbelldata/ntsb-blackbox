import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

vi.mock("../lib/api", () => ({ fetchDatasetCard: vi.fn() }));

import { fetchDatasetCard } from "../lib/api";
import { Data } from "./Data";

beforeEach(() => {
  vi.mocked(fetchDatasetCard).mockResolvedValue({
    source: { name: "US NTSB aviation accident final reports", provider: "NTSB via Zenodo", license: "Public domain" },
    coverage: { start_year: 2016, end_year: 2023, known_gaps: ["2020 and 2021 are absent from this dataset."] },
    caveats: ["fatal_injury_count > 0 is the reliable fatal signal."],
    table: "accidents",
    schema: [
      { name: "event_year", dtype: "INTEGER", description: "Year extracted from event_date." },
      { name: "make", dtype: "TEXT", description: "Aircraft make/manufacturer as reported." }
    ],
    counts: { accident_count: 12408, tracked_source_count: null },
    database: "sqlite",
    ready: true,
    latest_ingest: null
  });
});

describe("Data page", () => {
  it("renders provenance, a known gap, a schema row, and a caveat", async () => {
    render(<Data />);
    await waitFor(() =>
      expect(screen.getByText("US NTSB aviation accident final reports")).toBeInTheDocument()
    );
    expect(screen.getByText(/2020 and 2021 are absent/)).toBeInTheDocument();
    expect(screen.getByText("event_year")).toBeInTheDocument();
    expect(screen.getByText(/reliable fatal signal/)).toBeInTheDocument();
  });

  it("renders the latest-ingest section when present", async () => {
    vi.mocked(fetchDatasetCard).mockResolvedValueOnce({
      source: { name: "NTSB", provider: "Zenodo", license: "Public domain" },
      coverage: { start_year: 2016, end_year: 2023, known_gaps: ["gap"] },
      caveats: ["caveat"],
      table: "accidents",
      schema: [{ name: "make", dtype: "TEXT", description: "d" }],
      counts: { accident_count: 1, tracked_source_count: 42 },
      database: "sqlite",
      ready: true,
      latest_ingest: { source_name: "ntsb-csv", status: "success", finished_at: "2026-06-01T00:00:00Z" }
    });
    render(<Data />);
    await waitFor(() => expect(screen.getByText("Latest ingest")).toBeInTheDocument());
    expect(screen.getByText("ntsb-csv")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });
});
