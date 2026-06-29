import { useEffect, useState } from "react";
import { Eyebrow, Skeleton } from "../components/primitives";
import { fetchDatasetCard, type DatasetCard } from "../lib/api";

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-rule py-7">
      <h2 className="font-display text-xl font-medium text-ink">{title}</h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function MetaRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-rule py-2 last:border-0">
      <dt className="eyebrow">{label}</dt>
      <dd className="data text-sm text-ink">{value}</dd>
    </div>
  );
}

export function TheData() {
  const [card, setCard] = useState<DatasetCard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchDatasetCard()
      .then((data) => !cancelled && setCard(data))
      .catch((err) => !cancelled && setError(err instanceof Error ? err.message : "Failed to load dataset card"))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-5 py-12 sm:px-8 sm:py-16">
      <header className="measure mb-6">
        <Eyebrow>Provenance &amp; method</Eyebrow>
        <h1 className="mt-3 font-display text-4xl font-medium text-ink sm:text-5xl">The data</h1>
        <p className="lede mt-4">
          Where every figure comes from, and what it does not cover. Being explicit about the limits
          is part of trusting the numbers.
        </p>
      </header>

      {error && (
        <div className="rounded-lg border border-danger/40 bg-surface p-4 text-sm text-danger">{error}</div>
      )}
      {loading && <Skeleton className="h-64 w-full" />}

      {card && (
        <>
          <Block title="Source">
            <p className="font-display text-lg text-ink">{card.source.name}</p>
            <dl className="mt-3">
              <MetaRow label="Provider" value={card.source.provider} />
              <MetaRow label="License" value={card.source.license} />
              <MetaRow label="Coverage" value={`${card.coverage.start_year}–${card.coverage.end_year}`} />
              {card.ready && card.counts.accident_count != null && (
                <MetaRow label="Rows" value={card.counts.accident_count.toLocaleString("en-US")} />
              )}
            </dl>
          </Block>

          <Block title="Known gaps">
            <ul className="space-y-2">
              {card.coverage.known_gaps.map((gap) => (
                <li key={gap} className="measure flex gap-2 text-sm text-ink-soft">
                  <span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-amber" />
                  {gap}
                </li>
              ))}
            </ul>
          </Block>

          <Block title={`Schema · ${card.table}`}>
            <div className="overflow-x-auto rounded-md border border-rule">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken text-left">
                    <th className="eyebrow px-3 py-2">Column</th>
                    <th className="eyebrow px-3 py-2">Type</th>
                    <th className="eyebrow px-3 py-2">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {card.schema.map((col) => (
                    <tr key={col.name} className="border-b border-rule last:border-0 align-top">
                      <td className="data px-3 py-2 text-accent">{col.name}</td>
                      <td className="data px-3 py-2 text-muted">{col.dtype}</td>
                      <td className="px-3 py-2 text-ink-soft">{col.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Block>

          {card.latest_ingest && (
            <Block title="Latest ingest">
              <dl>
                {card.latest_ingest.source_name != null && (
                  <MetaRow label="Source" value={String(card.latest_ingest.source_name)} />
                )}
                {card.latest_ingest.status != null && (
                  <MetaRow label="Status" value={String(card.latest_ingest.status)} />
                )}
                {card.latest_ingest.finished_at != null && (
                  <MetaRow label="Finished" value={String(card.latest_ingest.finished_at)} />
                )}
                {card.counts.tracked_source_count != null && (
                  <MetaRow label="Tracked sources" value={card.counts.tracked_source_count.toLocaleString("en-US")} />
                )}
              </dl>
            </Block>
          )}

          <Block title="Caveats">
            <ul className="space-y-2">
              {card.caveats.map((caveat) => (
                <li key={caveat} className="measure flex gap-2 text-sm text-ink-soft">
                  <span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-amber" />
                  {caveat}
                </li>
              ))}
            </ul>
          </Block>
        </>
      )}
    </div>
  );
}
