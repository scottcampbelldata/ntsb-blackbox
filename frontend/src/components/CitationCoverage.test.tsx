import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("../lib/api", () => ({ fetchContext: vi.fn() }));

import { fetchContext } from "../lib/api";
import { CitationCoverage } from "./CitationCoverage";

const citation = {
  ntsb_no: "ABC123",
  score: 0.9,
  matched_passage: "…",
  probable_cause: "pilot error",
  make: "Cessna",
  city: "Reno"
};

beforeEach(() => vi.mocked(fetchContext).mockReset());

describe("CitationCoverage", () => {
  it("does not fetch until expanded, then lists articles", async () => {
    vi.mocked(fetchContext).mockResolvedValue({
      query: "Cessna aviation accident Reno",
      source: "gdelt",
      articles: [{ title: "Crash report", url: "https://news.x/1", domain: "news.x", date: "20190101" }],
      search_url: "https://news.google.com/search?q=x"
    });

    render(<CitationCoverage citation={citation} />);
    expect(fetchContext).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /related coverage/i }));
    await waitFor(() => expect(screen.getByText("Crash report")).toBeInTheDocument());
    expect(fetchContext).toHaveBeenCalledTimes(1);
  });

  it("shows a search link when there are no articles", async () => {
    vi.mocked(fetchContext).mockResolvedValue({
      query: "Piper aviation accident",
      source: "fallback",
      articles: [],
      search_url: "https://news.google.com/search?q=piper"
    });

    render(<CitationCoverage citation={citation} />);
    fireEvent.click(screen.getByRole("button", { name: /related coverage/i }));
    await waitFor(() => expect(screen.getByRole("link", { name: /search news/i })).toBeInTheDocument());
  });

  it("shows unavailable on error and retries on reopen", async () => {
    vi.mocked(fetchContext).mockRejectedValueOnce(new Error("network"));
    render(<CitationCoverage citation={citation} />);

    fireEvent.click(screen.getByRole("button", { name: /related coverage/i }));
    await waitFor(() => expect(screen.getByText(/coverage unavailable/i)).toBeInTheDocument());

    // collapse, then reopen -> should retry the fetch (loaded was not set on error)
    fireEvent.click(screen.getByRole("button", { name: /related coverage/i }));
    vi.mocked(fetchContext).mockResolvedValueOnce({
      query: "q", source: "fallback", articles: [], search_url: "https://news.google.com/search?q=x"
    });
    fireEvent.click(screen.getByRole("button", { name: /related coverage/i }));

    await waitFor(() => expect(screen.getByRole("link", { name: /search news/i })).toBeInTheDocument());
    expect(fetchContext).toHaveBeenCalledTimes(2);
  });
});
