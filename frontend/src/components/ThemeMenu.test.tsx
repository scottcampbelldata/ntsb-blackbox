import { describe, it, expect, beforeEach } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { ThemeProvider } from "../theme/useTheme";
import { ThemeMenu } from "./ThemeMenu";

function renderMenu() {
  return render(
    <ThemeProvider>
      <ThemeMenu />
    </ThemeProvider>
  );
}

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

describe("ThemeMenu", () => {
  it("offers System, Light, and Dark, with System active by default", () => {
    const { getByRole } = renderMenu();
    expect(getByRole("button", { name: "System" })).toHaveAttribute("aria-pressed", "true");
    expect(getByRole("button", { name: "Light" })).toHaveAttribute("aria-pressed", "false");
    expect(getByRole("button", { name: "Dark" })).toHaveAttribute("aria-pressed", "false");
  });

  it("applies dark and persists the choice when Dark is picked", () => {
    const { getByRole } = renderMenu();
    fireEvent.click(getByRole("button", { name: "Dark" }));
    expect(getByRole("button", { name: "Dark" })).toHaveAttribute("aria-pressed", "true");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(window.localStorage.getItem("blackbox-theme")).toBe("dark");
  });
});
