import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { NewsPanel, CitationNews } from "./NewsPanel";
import type { RelatedCoverage } from "../lib/api";

const citation = {
  ntsb_no: "ABC123",
  score: 0.9,
  matched_passage: "…",
  probable_cause: "pilot error",
  make: "Cessna",
  city: "Reno"
};

const coverage: RelatedCoverage = {
  query: "Cessna aviation accident Reno",
  source: "gdelt",
  articles: [{ title: "Crash makes headlines", url: "https://news.x/1", domain: "news.x", date: "20190101" }],
  search_url: "https://news.google.com/search?q=x"
};

describe("NewsPanel", () => {
  it("lists found articles with a count and the source accident", () => {
    const { getByText } = render(
      <NewsPanel citations={[citation]} byId={{ ABC123: coverage }} loading={false} />
    );
    expect(getByText("In the news (1)")).toBeInTheDocument();
    expect(getByText("Crash makes headlines")).toBeInTheDocument();
    expect(getByText(/ABC123/)).toBeInTheDocument();
  });

  it("shows a searching note while loading with nothing yet", () => {
    const { getByText } = render(<NewsPanel citations={[citation]} byId={{}} loading={true} />);
    expect(getByText(/Searching news coverage/)).toBeInTheDocument();
  });

  it("shows an honest empty note when no coverage was found", () => {
    const { getByText } = render(<NewsPanel citations={[citation]} byId={{}} loading={false} />);
    expect(getByText(/No external news coverage found/)).toBeInTheDocument();
  });

  it("renders nothing when there are no citations", () => {
    const { container } = render(<NewsPanel citations={[]} byId={{}} loading={false} />);
    expect(container.firstChild).toBeNull();
  });
});

describe("CitationNews", () => {
  it("renders inline articles when coverage exists", () => {
    const { getByText } = render(<CitationNews coverage={coverage} />);
    expect(getByText("In the news")).toBeInTheDocument();
    expect(getByText("Crash makes headlines")).toBeInTheDocument();
  });

  it("renders nothing when coverage is missing or empty", () => {
    const { container: a } = render(<CitationNews coverage={undefined} />);
    expect(a.firstChild).toBeNull();
    const { container: b } = render(<CitationNews coverage={{ ...coverage, articles: [] }} />);
    expect(b.firstChild).toBeNull();
  });
});
