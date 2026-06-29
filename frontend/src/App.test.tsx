import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { act } from "react";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider } from "./theme/useTheme";

vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 800, height: 340 }}>{children}</div>
    )
  };
});

vi.mock("./lib/api", () => ({
  fetchDataset: vi.fn().mockResolvedValue({
    accident_count: 0,
    fatal_count: 0,
    min_year: 2016,
    max_year: 2024,
    distinct_makes: 0
  }),
  fetchAnalyses: vi.fn().mockResolvedValue([]),
  fetchAnalysis: vi.fn()
}));

import App from "./App";

function renderAt(path: string) {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </ThemeProvider>
  );
}

describe("App routing", () => {
  it("renders the Findings hero at /", async () => {
    let getByRole!: ReturnType<typeof render>["getByRole"];
    await act(async () => {
      ({ getByRole } = renderAt("/"));
    });
    expect(getByRole("heading", { name: /the ones that kill happen aloft/i })).toBeInTheDocument();
  });

  it("renders the Ask page at /ask", async () => {
    let getByRole!: ReturnType<typeof render>["getByRole"];
    await act(async () => {
      ({ getByRole } = renderAt("/ask"));
    });
    expect(getByRole("heading", { name: "Ask the record" })).toBeInTheDocument();
  });
});
