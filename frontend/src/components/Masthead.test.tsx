import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider } from "../theme/useTheme";
import { Masthead } from "./Masthead";

function renderMasthead() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <Masthead />
      </MemoryRouter>
    </ThemeProvider>
  );
}

describe("Masthead", () => {
  it("links to all three sections and exposes the theme control", () => {
    const { getByRole } = renderMasthead();
    expect(getByRole("link", { name: /findings/i })).toBeInTheDocument();
    expect(getByRole("link", { name: /ask the record/i })).toBeInTheDocument();
    expect(getByRole("link", { name: /the data/i })).toBeInTheDocument();
    expect(getByRole("group", { name: /color theme/i })).toBeInTheDocument();
  });
});
