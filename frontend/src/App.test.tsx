import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { act } from "react";
import { MemoryRouter } from "react-router-dom";

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
  fetchDataset: vi.fn().mockResolvedValue({
    accident_count: 0, fatal_count: 0, min_year: 2016, max_year: 2023, distinct_makes: 0
  }),
  fetchAnalyses: vi.fn().mockResolvedValue([]),
  fetchAnalysis: vi.fn()
}));

import App from "./App";

describe("App routing", () => {
  it("renders the Dashboard at /", async () => {
    let getByRole!: ReturnType<typeof render>["getByRole"];
    await act(async () => {
      ({ getByRole } = render(
        <MemoryRouter initialEntries={["/"]}>
          <App />
        </MemoryRouter>
      ));
    });
    expect(getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  });

  it("renders the Ask page at /ask", async () => {
    let getByPlaceholderText!: ReturnType<typeof render>["getByPlaceholderText"];
    await act(async () => {
      ({ getByPlaceholderText } = render(
        <MemoryRouter initialEntries={["/ask"]}>
          <App />
        </MemoryRouter>
      ));
    });
    expect(getByPlaceholderText(/ask about the loaded ntsb/i)).toBeInTheDocument();
  });
});
