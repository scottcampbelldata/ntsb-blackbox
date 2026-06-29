import { ChartView } from "./ChartView";
import { Tabs, type TabItem } from "./Tabs";
import { NewsPanel, CitationNews } from "./NewsPanel";
import { Eyebrow } from "./primitives";
import { useRelatedCoverage } from "../lib/useRelatedCoverage";
import type { RelatedCoverage } from "../lib/api";
import type { AskResponse } from "../types";

function Byline({ response }: { response: AskResponse }) {
  return (
    <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1.5">
      <span className="rounded-full border border-accent px-2 py-0.5 font-mono text-[0.65rem] font-medium uppercase tracking-wider text-accent">
        {response.route.route}
      </span>
      <span className="data text-xs text-muted">
        {Math.round(response.confidence * 100)}% confidence
      </span>
    </div>
  );
}

function ResultTable({ table }: { table: NonNullable<AskResponse["table"]> }) {
  return (
    <div className="overflow-x-auto rounded-md border border-rule">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-rule bg-surface-sunken text-left">
            {table.columns.map((c) => (
              <th key={c} className="data px-3 py-2 text-xs font-medium uppercase tracking-wide text-muted">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, i) => (
            <tr key={i} className="border-b border-rule last:border-0">
              {table.columns.map((c) => (
                <td key={c} className="data px-3 py-2 text-ink-soft">
                  {String(row[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function References({
  citations,
  coverage
}: {
  citations: AskResponse["citations"];
  coverage: Record<string, RelatedCoverage>;
}) {
  return (
    <ol className="space-y-4">
      {citations.map((c, i) => (
        <li key={c.ntsb_no} className="flex gap-3">
          <span className="data mt-0.5 shrink-0 text-xs text-muted">{i + 1}</span>
          <article className="min-w-0 flex-1">
            {c.report_url ? (
              <a
                href={c.report_url}
                target="_blank"
                rel="noreferrer"
                className="data text-sm text-accent underline decoration-rule-strong underline-offset-2 hover:decoration-accent"
              >
                {c.ntsb_no}
              </a>
            ) : (
              <span className="data text-sm text-ink">{c.ntsb_no}</span>
            )}
            <p className="mt-1 text-sm leading-relaxed text-ink-soft">
              {c.probable_cause || c.matched_passage}
            </p>
            <CitationNews coverage={coverage[c.ntsb_no]} />
          </article>
        </li>
      ))}
    </ol>
  );
}

export function AnswerArticle({ response }: { response: AskResponse | null }) {
  const { byId: coverage, loading: coverageLoading } = useRelatedCoverage(response?.citations ?? []);
  if (!response) return null;

  const tabs: TabItem[] = [];
  if (response.sql) {
    tabs.push({
      id: "sql",
      label: "SQL",
      content: (
        <pre className="data overflow-x-auto rounded-md bg-surface-sunken p-3 text-xs leading-relaxed text-ink-soft">
          {response.sql}
        </pre>
      )
    });
  }
  if (response.table) {
    tabs.push({ id: "table", label: "Table", content: <ResultTable table={response.table} /> });
  }
  if (response.citations.length > 0) {
    tabs.push({
      id: "citations",
      label: `Citations (${response.citations.length})`,
      content: <References citations={response.citations} coverage={coverage} />
    });
  }
  tabs.push({
    id: "audit",
    label: "Audit",
    content: (
      <ol className="space-y-2">
        {response.audit.map((e, i) => (
          <li key={`${e.step}-${i}`} className="flex gap-3 text-sm">
            <span className="data shrink-0 text-xs text-accent">{e.step}</span>
            <span className="text-ink-soft">{e.detail}</span>
          </li>
        ))}
      </ol>
    )
  });

  return (
    <article className="mt-8 space-y-6">
      <header>
        <Eyebrow>The answer</Eyebrow>
        <p className="lede mt-2">{response.answer}</p>
        <Byline response={response} />
      </header>

      {response.chart_spec && response.table && (
        <figure className="rounded-lg border border-rule bg-surface p-5">
          <ChartView spec={response.chart_spec} rows={response.table.rows} />
        </figure>
      )}

      {response.citations.length > 0 && (
        <NewsPanel citations={response.citations} byId={coverage} loading={coverageLoading} />
      )}

      <section className="rounded-lg border border-rule bg-surface p-5">
        <Eyebrow>How this answer was produced</Eyebrow>
        <div className="mt-3">
          <Tabs tabs={tabs} />
        </div>
      </section>

      <section>
        <Eyebrow>Limitations</Eyebrow>
        {response.limitations.length > 0 ? (
          <ul className="mt-2 space-y-1.5">
            {response.limitations.map((item) => (
              <li key={item} className="measure flex gap-2 text-sm text-muted">
                <span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-amber" />
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-muted">None reported.</p>
        )}
      </section>
    </article>
  );
}
