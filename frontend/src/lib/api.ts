import type { ChartRow } from "./vegaLiteToRecharts";
import type { AskResponse, Provider } from "../types";

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

export type AskRequestParams = {
  question: string;
  provider: Provider;
  model: string;
  apiKey: string | null;
  sessionId: string;
};

export async function ask(params: AskRequestParams): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Session-ID": params.sessionId },
    body: JSON.stringify({
      question: params.question,
      provider: params.provider,
      model: params.model,
      api_key: params.apiKey,
      chart_preference: "auto",
      session_id: params.sessionId
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || "Request failed");
  return data as AskResponse;
}

export async function clearKey(params: { provider: Provider; sessionId: string }): Promise<void> {
  await fetch(`${API_BASE}/api/keys/clear`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Session-ID": params.sessionId },
    body: JSON.stringify({ provider: params.provider, session_id: params.sessionId })
  });
}

export type SchemaColumn = { name: string; dtype: string; description: string };

export type DatasetCard = {
  source: { name: string; provider: string; license: string };
  coverage: { start_year: number; end_year: number; known_gaps: string[] };
  caveats: string[];
  table: string;
  schema: SchemaColumn[];
  counts: { accident_count: number | null; tracked_source_count: number | null };
  database: string | null;
  ready: boolean;
  latest_ingest: Record<string, unknown> | null;
};

export async function fetchDatasetCard(): Promise<DatasetCard> {
  return getJson<DatasetCard>("/api/dataset/card");
}
