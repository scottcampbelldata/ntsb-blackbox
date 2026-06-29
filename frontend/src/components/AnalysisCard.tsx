import { ChartView } from "./ChartView";
import type { AnalysisResult } from "../lib/api";

export function AnalysisCard({
  analysis,
  featured = false
}: {
  analysis: AnalysisResult;
  featured?: boolean;
}) {
  return (
    <section className={`analysis-card${featured ? " analysis-card-featured" : ""}`}>
      <h3 className="analysis-title">{analysis.label}</h3>
      <ChartView spec={analysis.chart_spec} rows={analysis.rows} />
      {analysis.note && <p className="analysis-note">{analysis.note}</p>}
      <details className="sql-disclosure">
        <summary>View SQL</summary>
        <pre>{analysis.sql}</pre>
      </details>
    </section>
  );
}
