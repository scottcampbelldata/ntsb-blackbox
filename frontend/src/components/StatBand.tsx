import type { DatasetKpis } from "../lib/api";

function Figure({
  label,
  value,
  sub,
  accent = false
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <div className="px-5 py-4 first:pl-0">
      <p className="eyebrow">{label}</p>
      <p
        className={`data mt-1.5 text-3xl font-medium leading-none sm:text-4xl ${
          accent ? "text-accent" : "text-ink"
        }`}
      >
        {value}
      </p>
      {sub && <p className="mt-1.5 text-xs text-muted">{sub}</p>}
    </div>
  );
}

export function StatBand({ kpis }: { kpis: DatasetKpis }) {
  const years =
    kpis.min_year != null && kpis.max_year != null ? `${kpis.min_year}-${kpis.max_year}` : "N/A";
  const rate =
    kpis.accident_count > 0 ? `${((kpis.fatal_count / kpis.accident_count) * 100).toFixed(1)}% of accidents` : undefined;

  return (
    <div className="grid grid-cols-2 divide-rule border-y border-rule sm:grid-cols-4 sm:divide-x">
      <Figure label="Accidents" value={kpis.accident_count.toLocaleString("en-US")} sub="final reports" />
      <Figure label="Fatal" value={kpis.fatal_count.toLocaleString("en-US")} sub={rate} accent />
      <Figure label="Years covered" value={years} sub="event date" />
      <Figure label="Aircraft makes" value={kpis.distinct_makes.toLocaleString("en-US")} sub="manufacturers" />
    </div>
  );
}
