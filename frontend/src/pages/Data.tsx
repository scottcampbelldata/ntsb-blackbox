import { useEffect, useState } from "react";
import { fetchDatasetCard, type DatasetCard } from "../lib/api";

export function Data() {
  const [card, setCard] = useState<DatasetCard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchDatasetCard()
      .then((data) => {
        if (!cancelled) setCard(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load dataset card");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="workspace">
      <section className="main-column">
        <h1 className="page-title">Data</h1>
        <p className="subtitle">
          Provenance and known limits of the corpus behind every answer. Being explicit about what
          the data does and doesn't cover is part of trusting the numbers.
        </p>

        {loading && <div className="loading">Loading dataset card…</div>}
        {error && <div className="error">{error}</div>}

        {card && (
          <>
            <section className="card-block">
              <h2>Source</h2>
              <p className="source-name">{card.source.name}</p>
              <dl className="meta-list">
                <div><dt>Provider</dt><dd>{card.source.provider}</dd></div>
                <div><dt>License</dt><dd>{card.source.license}</dd></div>
                <div><dt>Coverage</dt><dd className="tabular">{card.coverage.start_year}–{card.coverage.end_year}</dd></div>
                {card.ready && card.counts.accident_count != null && (
                  <div><dt>Rows</dt><dd className="tabular">{card.counts.accident_count.toLocaleString("en-US")}</dd></div>
                )}
              </dl>
            </section>

            <section className="card-block">
              <h2>Known gaps</h2>
              <ul className="gap-list">
                {card.coverage.known_gaps.map((gap) => <li key={gap}>{gap}</li>)}
              </ul>
            </section>

            <section className="card-block">
              <h2>Schema — <code>{card.table}</code></h2>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr><th>Column</th><th>Type</th><th>Description</th></tr>
                  </thead>
                  <tbody>
                    {card.schema.map((col) => (
                      <tr key={col.name}>
                        <td><code>{col.name}</code></td>
                        <td>{col.dtype}</td>
                        <td>{col.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {card.latest_ingest && (
              <section className="card-block">
                <h2>Latest ingest</h2>
                <dl className="meta-list">
                  {card.latest_ingest.source_name != null && (
                    <div><dt>Source</dt><dd>{String(card.latest_ingest.source_name)}</dd></div>
                  )}
                  {card.latest_ingest.status != null && (
                    <div><dt>Status</dt><dd>{String(card.latest_ingest.status)}</dd></div>
                  )}
                  {card.latest_ingest.finished_at != null && (
                    <div><dt>Finished</dt><dd>{String(card.latest_ingest.finished_at)}</dd></div>
                  )}
                  {card.counts.tracked_source_count != null && (
                    <div><dt>Tracked sources</dt><dd className="tabular">{card.counts.tracked_source_count.toLocaleString("en-US")}</dd></div>
                  )}
                </dl>
              </section>
            )}

            <section className="card-block">
              <h2>Caveats</h2>
              <ul className="gap-list">
                {card.caveats.map((caveat) => <li key={caveat}>{caveat}</li>)}
              </ul>
            </section>
          </>
        )}
      </section>
    </div>
  );
}
