import type { DatasetKpis } from "../lib/api";

// The dataset at a glance, set as the summary aside the project pages use.
// Same four figures the page has always shown, each with its unit line.
function Row({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
      {sub && <dd className="glance-sub">{sub}</dd>}
    </div>
  );
}

export function StatBand({ kpis }: { kpis: DatasetKpis }) {
  const years =
    kpis.min_year != null && kpis.max_year != null ? `${kpis.min_year}-${kpis.max_year}` : "N/A";
  const rate =
    kpis.accident_count > 0 ? `${((kpis.fatal_count / kpis.accident_count) * 100).toFixed(1)}% of accidents` : undefined;

  return (
    <dl className="glance" aria-label="The dataset at a glance">
      <Row label="Accidents" value={kpis.accident_count.toLocaleString("en-US")} sub="final reports" />
      <Row label="Fatal" value={kpis.fatal_count.toLocaleString("en-US")} sub={rate} />
      <Row label="Years covered" value={years} sub="event date" />
      <Row label="Aircraft makes" value={kpis.distinct_makes.toLocaleString("en-US")} sub="manufacturers" />
    </dl>
  );
}
