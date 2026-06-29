import { ChartView } from "./ChartView";
import { Disclosure, Eyebrow } from "./primitives";
import type { AnalysisResult } from "../lib/api";

// The kicker states what the axis measures — a count, a share, or a time
// series — so the reader knows how to read the bars before reading them.
function kickerFor(analysis: AnalysisResult): string {
  if (analysis.key.startsWith("fatal_rate") || analysis.columns.includes("fatal_rate_pct")) {
    return "Share fatal · %";
  }
  if (analysis.columns[0] === "year") return "Count · by year";
  return "Count";
}

export function FigureCard({
  analysis,
  featured = false
}: {
  analysis: AnalysisResult;
  featured?: boolean;
}) {
  return (
    <figure
      className={`flex flex-col rounded-lg border border-rule bg-surface p-5 shadow-card sm:p-6 ${
        featured ? "gap-4" : "gap-3"
      }`}
    >
      <div>
        <Eyebrow>{kickerFor(analysis)}</Eyebrow>
        <h3
          className={`mt-1 font-display leading-tight text-ink ${
            featured ? "text-2xl sm:text-[1.7rem]" : "text-xl"
          }`}
        >
          {analysis.label}
        </h3>
      </div>

      <ChartView spec={analysis.chart_spec} rows={analysis.rows} height={featured ? 400 : 300} />

      {analysis.note && (
        <figcaption className="measure text-sm leading-relaxed text-muted">
          {analysis.note}
        </figcaption>
      )}

      <Disclosure label="View SQL">
        <pre className="data overflow-x-auto rounded-md bg-surface-sunken p-3 text-xs leading-relaxed text-ink-soft">
          {analysis.sql}
        </pre>
      </Disclosure>
    </figure>
  );
}
