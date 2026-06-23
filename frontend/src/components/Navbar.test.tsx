import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Navbar } from "./Navbar";

describe("Navbar", () => {
  it("renders the three section links and a theme toggle", () => {
    const { getByRole } = render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    expect(getByRole("link", { name: /dashboard/i })).toBeInTheDocument();
    expect(getByRole("link", { name: /ask/i })).toBeInTheDocument();
    expect(getByRole("link", { name: /data/i })).toBeInTheDocument();
    expect(getByRole("button", { name: /theme/i })).toBeInTheDocument();
  });
});
