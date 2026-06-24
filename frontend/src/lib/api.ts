import type { ChartRow } from "./vegaLiteToRecharts";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export type AnalysisListItem = { key: string; label: string };

export type AnalysisResult = {
  key: string;
  label: string;
  sql: string;
  columns: string[];
  rows: ChartRow[];
  chart_spec: Record<string, unknown> | null;
};

export type DatasetKpis = {
  accident_count: number;
  fatal_count: number;
  min_year: number | null;
  max_year: number | null;
  distinct_makes: number;
};

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchDataset(): Promise<DatasetKpis> {
  return getJson<DatasetKpis>("/api/dataset");
}

export async function fetchAnalyses(): Promise<AnalysisListItem[]> {
  const data = await getJson<{ analyses: AnalysisListItem[] }>("/api/analyses");
  return data.analyses;
}

export async function fetchAnalysis(key: string): Promise<AnalysisResult> {
  return getJson<AnalysisResult>(`/api/analyses/${key}`);
}
