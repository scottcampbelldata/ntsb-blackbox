import { useState } from "react";
import { fetchContext, type RelatedCoverage } from "../lib/api";
import type { AskResponse } from "../types";

export function CitationCoverage({ citation }: { citation: AskResponse["citations"][number] }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<RelatedCoverage | null>(null);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && !loaded) {
      setLoading(true);
      try {
        const result = await fetchContext({
          make: citation.make,
          model: citation.model,
          city: citation.city,
          state: citation.state,
          year: citation.event_year
        });
        setData(result);
        setLoaded(true);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <div className="coverage">
      <button type="button" className="coverage-toggle" aria-expanded={open} onClick={toggle}>
        Related coverage
      </button>
      {open && (
        <div className="coverage-body">
          {loading && <span className="coverage-loading">Loading…</span>}
          {!loading && data && data.articles.length > 0 && (
            <ul className="coverage-list">
              {data.articles.map((article, index) => (
                <li key={article.url ?? `row-${index}`}>
                  {article.url ? (
                    <a href={article.url} target="_blank" rel="noreferrer">
                      {article.title || article.domain || article.url}
                    </a>
                  ) : (
                    <span>{article.title || ""}</span>
                  )}
                  {article.domain && <span className="coverage-domain"> · {article.domain}</span>}
                </li>
              ))}
            </ul>
          )}
          {!loading && data && data.articles.length === 0 && (
            <a className="coverage-search" href={data.search_url} target="_blank" rel="noreferrer">
              Search news for this accident
            </a>
          )}
          {!loading && !data && <span className="coverage-empty">Coverage unavailable.</span>}
        </div>
      )}
    </div>
  );
}
