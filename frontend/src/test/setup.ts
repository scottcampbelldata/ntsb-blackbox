import "@testing-library/jest-dom";
import { vi } from "vitest";

// jsdom has no matchMedia; the ThemeProvider needs it. Default to light
// (matches: false) with working add/removeEventListener so listeners are safe.
if (!window.matchMedia) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn()
  }));
}
