import { useEffect, useState } from "react";
import { StatBand } from "../components/StatBand";
import { FigureCard } from "../components/FigureCard";
import { Eyebrow, Skeleton, TraceRule } from "../components/primitives";
import {
  fetchAnalyses,
  fetchAnalysis,
  fetchDataset,
  type AnalysisResult,
  type DatasetKpis
} from "../lib/api";

// The featured figure is the one that proves the headline: landing dominates the
// count, but the fatality rate inverts the order.
const HERO_KEY = "fatal_rate_by_phase";

export function Findings() {
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
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load findings");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const hero = analyses.find((a) => a.key === HERO_KEY) ?? analyses[0];
  const rest = analyses.filter((a) => a !== hero);

  return (
    <div className="mx-auto max-w-6xl px-5 sm:px-8">
      <section className="flex flex-col pt-12 pb-2 sm:pt-20">
        <Eyebrow>US NTSB · aviation accident final reports</Eyebrow>
        <h1 className="mt-4 font-display font-medium text-ink" style={{ fontSize: "var(--text-display)", lineHeight: "var(--text-display--line-height)", letterSpacing: "var(--text-display--letter-spacing)" }}>
          Most accidents happen on landing. The ones that kill happen aloft.
        </h1>
        <p className="lede mt-6 measure">
          Black Box reads the record on US aviation safety. Every figure below is a live SQL query
          against the accident database. Expand “View SQL” on any chart to see exactly what produced
          the number.
        </p>
        <TraceRule className="mt-10" />
      </section>


      {error && (
        <div className="rounded-lg border border-danger/40 bg-surface p-4 text-sm text-danger">
          {error}
        </div>
      )}

      {loading && (
        <div className="space-y-8">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-[440px] w-full" />
          <div className="grid gap-6 sm:grid-cols-2">
            <Skeleton className="h-80 w-full" />
            <Skeleton className="h-80 w-full" />
          </div>
        </div>
      )}

      {kpis && <StatBand kpis={kpis} />}

      {hero && (
        <div className="mt-10">
          <FigureCard analysis={hero} featured />
        </div>
      )}

      {rest.length > 0 && (
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          {rest.map((analysis) => (
            <FigureCard key={analysis.key} analysis={analysis} />
          ))}
        </div>
      )}
    </div>
  );
}
