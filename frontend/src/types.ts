export type Provider = "openai" | "anthropic" | "gemini";

export type AskResponse = {
  session_id: string;
  question: string;
  route: {
    route: string;
    sql_triggers: string[];
    retrieval_triggers: string[];
    chart_triggers: string[];
  };
  answer: string;
  sql: string | null;
  table: { columns: string[]; rows: Record<string, string | number | null>[] } | null;
  chart_spec: Record<string, unknown> | null;
  citations: {
    ntsb_no: string;
    score: number;
    matched_passage: string;
    probable_cause: string;
    report_url?: string;
    event_year?: number;
    city?: string;
    state?: string;
    make?: string;
    model?: string;
  }[];
  confidence: number;
  limitations: string[];
  audit: { step: string; detail: string }[];
};
