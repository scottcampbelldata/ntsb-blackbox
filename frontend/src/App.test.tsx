import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";

describe("App routing", () => {
  it("renders the Dashboard at /", () => {
    const { getByRole } = render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );
    expect(getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  });

  it("renders the Ask page at /ask", () => {
    const { getByPlaceholderText } = render(
      <MemoryRouter initialEntries={["/ask"]}>
        <App />
      </MemoryRouter>
    );
    expect(getByPlaceholderText(/ask about the loaded ntsb/i)).toBeInTheDocument();
  });
});
