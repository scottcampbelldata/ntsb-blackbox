import type { RelatedArticle, RelatedCoverage } from "../lib/api";
import type { AskResponse } from "../types";

type Citation = AskResponse["citations"][number];

function ArticleLink({ article }: { article: RelatedArticle }) {
  if (!article.url) return <span>{article.title || ""}</span>;
  return (
    <a href={article.url} target="_blank" rel="noreferrer">
      {article.title || article.domain || article.url}
    </a>
  );
}

// Prominent, always-visible roundup of any real news stories GDELT returned for
// the accidents behind the answer. This is the discoverable surface: the user
// sees news without opening a tab or clicking a per-record button.
export function NewsPanel({
  citations,
  byId,
  loading
}: {
  citations: Citation[];
  byId: Record<string, RelatedCoverage>;
  loading: boolean;
}) {
  if (citations.length === 0) return null;

  const withNews = citations
    .map((c) => ({ citation: c, coverage: byId[c.ntsb_no] }))
    .filter((entry) => entry.coverage && entry.coverage.articles.length > 0);

  const total = withNews.reduce((sum, entry) => sum + entry.coverage!.articles.length, 0);

  return (
    <section className="news-panel">
      <h4 className="news-panel-title">In the news{total > 0 ? ` (${total})` : ""}</h4>
      {loading && total === 0 && (
        <p className="news-empty">Searching news coverage for these accidents…</p>
      )}
      {!loading && total === 0 && (
        <p className="news-empty">No external news coverage found for these accidents.</p>
      )}
      {total > 0 && (
        <ul className="news-list">
          {withNews.flatMap(({ citation, coverage }) =>
            coverage!.articles.map((article, index) => (
              <li key={`${citation.ntsb_no}-${index}`} className="news-item">
                <ArticleLink article={article} />
                <span className="news-meta">
                  {article.domain ? `${article.domain} · ` : ""}
                  {citation.ntsb_no}
                </span>
              </li>
            ))
          )}
        </ul>
      )}
    </section>
  );
}

// The same coverage shown inline beneath a single citation, so the news stays
// associated with its record. Renders nothing when that accident has no news.
export function CitationNews({ coverage }: { coverage: RelatedCoverage | undefined }) {
  if (!coverage || coverage.articles.length === 0) return null;
  return (
    <div className="coverage">
      <span className="coverage-label">In the news</span>
      <ul className="coverage-list">
        {coverage.articles.map((article, index) => (
          <li key={article.url ?? `row-${index}`}>
            <ArticleLink article={article} />
            {article.domain && <span className="coverage-domain"> · {article.domain}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
