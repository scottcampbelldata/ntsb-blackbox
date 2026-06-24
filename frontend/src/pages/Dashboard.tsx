import { useEffect, useState } from "react";
import { KpiStrip } from "../components/KpiStrip";
import { AnalysisCard } from "../components/AnalysisCard";
import { fetchAnalyses, fetchAnalysis, fetchDataset, type AnalysisResult, type DatasetKpis } from "../lib/api";

const HERO_KEY = "accidents_by_year";

export function Dashboard() {
  const [kpis, setKpis] = useState<DatasetKpis | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [dataset, list] = await Promise.all([fetchDataset(), fetchAnalyses()]);
        const results = await Promise.all(list.map((item) => fetchAnalysis(item.key)));
        if (cancelled) return;
        setKpis(dataset);
        setAnalyses(results);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load dashboard");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const hero = analyses.find((a) => a.key === HERO_KEY);
  const rest = analyses.filter((a) => a.key !== HERO_KEY);

  return (
    <div className="workspace">
      <section className="main-column">
        <h1 className="page-title">Dashboard</h1>
        <p className="subtitle">
          Question answering and analytics over NTSB aviation accident final reports. Every figure
          below is a real SQL query. Expand "View SQL" on any chart to see exactly what produced it.
        </p>

        {loading && <div className="loading">Loading analytics…</div>}
        {error && <div className="error">{error}</div>}

        {kpis && <KpiStrip kpis={kpis} />}

        {hero && <AnalysisCard analysis={hero} featured />}

        {rest.length > 0 && (
          <div className="analysis-grid">
            {rest.map((analysis) => (
              <AnalysisCard key={analysis.key} analysis={analysis} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
