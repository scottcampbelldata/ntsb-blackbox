import type { DatasetKpis } from "../lib/api";

function Tile({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={`kpi-tile${accent ? " kpi-tile-accent" : ""}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value tabular">{value}</div>
    </div>
  );
}

export function KpiStrip({ kpis }: { kpis: DatasetKpis }) {
  const years =
    kpis.min_year != null && kpis.max_year != null ? `${kpis.min_year}-${kpis.max_year}` : "N/A";
  return (
    <div className="kpi-strip">
      <Tile label="Accidents" value={kpis.accident_count.toLocaleString("en-US")} />
      <Tile label="Fatal" value={kpis.fatal_count.toLocaleString("en-US")} accent />
      <Tile label="Years" value={years} />
      <Tile label="Makes" value={kpis.distinct_makes.toLocaleString("en-US")} />
    </div>
  );
}
