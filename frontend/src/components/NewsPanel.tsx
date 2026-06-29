import { Newspaper } from "lucide-react";
import { Eyebrow } from "./primitives";
import type { RelatedArticle, RelatedCoverage } from "../lib/api";
import type { AskResponse } from "../types";

type Citation = AskResponse["citations"][number];

function ArticleLink({ article }: { article: RelatedArticle }) {
  if (!article.url) return <span>{article.title || ""}</span>;
  return (
    <a
      href={article.url}
      target="_blank"
      rel="noreferrer"
      className="text-ink underline decoration-rule-strong underline-offset-2 hover:decoration-accent"
    >
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
    <section className="rounded-lg border border-rule bg-surface-sunken p-5">
      <h4 className="news-panel-title flex items-center gap-2">
        <Newspaper size={15} className="text-accent" aria-hidden="true" />
        <span className="eyebrow !text-ink">In the news{total > 0 ? ` (${total})` : ""}</span>
      </h4>
      {loading && total === 0 && (
        <p className="news-empty mt-3 text-sm text-muted">
          Searching news coverage for these accidents…
        </p>
      )}
      {!loading && total === 0 && (
        <p className="news-empty mt-3 text-sm text-muted">
          No external news coverage found for these accidents.
        </p>
      )}
      {total > 0 && (
        <ul className="mt-3 space-y-2.5">
          {withNews.flatMap(({ citation, coverage }) =>
            coverage!.articles.map((article, index) => (
              <li key={`${citation.ntsb_no}-${index}`} className="text-sm leading-snug">
                <ArticleLink article={article} />
                <span className="data mt-0.5 block text-xs text-muted">
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
    <div className="mt-2 border-l-2 border-rule pl-3">
      <Eyebrow>In the news</Eyebrow>
      <ul className="mt-1 space-y-1">
        {coverage.articles.map((article, index) => (
          <li key={article.url ?? `row-${index}`} className="text-sm">
            <ArticleLink article={article} />
            {article.domain && <span className="data text-xs text-muted"> · {article.domain}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
