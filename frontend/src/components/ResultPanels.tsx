import { BarChart3, Database, FileText, History, Link2, MessageSquareText, ShieldCheck } from "lucide-react";
import type { AskResponse } from "../types";

function PanelTitle({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="panel-title">
      {icon}
      <span>{children}</span>
    </div>
  );
}

function ChartPanel({ response }: { response: AskResponse }) {
  if (!response.chart_spec || !response.table) return null;
  const encoding = response.chart_spec.encoding as Record<string, any> | undefined;
  const xField = encoding?.x?.field as string | undefined;
  const yField = encoding?.y?.field as string | undefined;
  const title = response.chart_spec.title as string | undefined;
  const isHorizontalBar = response.chart_spec.mark === "bar" && xField && yField;
  const isLine = response.chart_spec.mark === "line" && xField && yField;

  return (
    <section className="panel">
      <PanelTitle icon={<BarChart3 size={18} />}>Chart</PanelTitle>
      <div className="chart-host">
        {isHorizontalBar && <BarChart rows={response.table.rows} labelField={yField} valueField={xField} title={title} />}
        {isLine && <LineChart rows={response.table.rows} xField={xField} yField={yField} title={title} />}
      </div>
    </section>
  );
}

function BarChart({
  rows,
  labelField,
  valueField,
  title
}: {
  rows: Record<string, string | number | null>[];
  labelField: string;
  valueField: string;
  title?: string;
}) {
  const values = rows.map((row) => Number(row[valueField] ?? 0)).filter((value) => Number.isFinite(value));
  const max = Math.max(...values, 1);
  const paddedMax = max * 1.12;

  return (
    <div className="native-chart">
      {title && <h3>{title}</h3>}
      <div className="bar-chart" style={{ ["--row-count" as string]: rows.length }}>
        {rows.map((row, index) => {
          const label = String(row[labelField] ?? "");
          const value = Number(row[valueField] ?? 0);
          const width = `${Math.max(1, Math.min(100, (value / paddedMax) * 100))}%`;
          return (
            <div className="bar-row" key={`${label}-${index}`}>
              <div className="bar-label" title={label}>{label}</div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width }} />
                <span className="bar-value">{Number.isInteger(value) ? value : value.toFixed(2)}</span>
              </div>
            </div>
          );
        })}
      </div>
      <div className="chart-axis-label">{valueField}</div>
    </div>
  );
}

function LineChart({
  rows,
  xField,
  yField,
  title
}: {
  rows: Record<string, string | number | null>[];
  xField: string;
  yField: string;
  title?: string;
}) {
  const points = rows.map((row) => ({
    x: String(row[xField] ?? ""),
    y: Number(row[yField] ?? 0)
  }));
  const max = Math.max(...points.map((point) => point.y), 1);
  const paddedMax = max * 1.12;
  const polyline = points
    .map((point, index) => {
      const x = points.length === 1 ? 50 : (index / (points.length - 1)) * 100;
      const y = 100 - (point.y / paddedMax) * 100;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="native-chart">
      {title && <h3>{title}</h3>}
      <svg className="line-chart" viewBox="0 0 100 100" preserveAspectRatio="none" role="img">
        <polyline points={polyline} fill="none" stroke="#5d7da8" strokeWidth="3" vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="line-labels">
        {points.map((point) => <span key={point.x}>{point.x}</span>)}
      </div>
      <div className="chart-axis-label">{yField}</div>
    </div>
  );
}

function AnswerPanel({ response }: { response: AskResponse }) {
  return (
    <section className="panel answer-panel">
      <PanelTitle icon={<ShieldCheck size={18} />}>Answer</PanelTitle>
      <p>{response.answer}</p>
      <div className="route-row">
        <span>{response.route.route.toUpperCase()}</span>
        <span>{Math.round(response.confidence * 100)}% confidence</span>
      </div>
    </section>
  );
}

function DetailPanel({ response }: { response: AskResponse }) {
  const topCitation = response.citations[0];
  return (
    <section className="panel detail-panel">
      <PanelTitle icon={<MessageSquareText size={18} />}>Answer</PanelTitle>
      <p>{response.answer}</p>
      {topCitation && (
        <div className="evidence-callout">
          <a href={topCitation.report_url} target="_blank" rel="noreferrer">
            {topCitation.ntsb_no}
          </a>
          <span>{topCitation.probable_cause || topCitation.matched_passage}</span>
        </div>
      )}
    </section>
  );
}

function RoutePanel({ response }: { response: AskResponse }) {
  return (
    <section className="panel route-panel">
      <PanelTitle icon={<ShieldCheck size={18} />}>Decision</PanelTitle>
      <div className="route-row">
        <span>{response.route.route.toUpperCase()}</span>
        <span>{Math.round(response.confidence * 100)}% confidence</span>
      </div>
      <p>
        {response.chart_spec
          ? "Structured result with a validated chart."
          : response.sql
            ? "Structured result without a chart."
            : "Narrative retrieval answer with cited report evidence."}
      </p>
    </section>
  );
}

function TablePanel({ response }: { response: AskResponse }) {
  if (!response.table) return null;
  return (
    <section className="panel">
      <PanelTitle icon={<Database size={18} />}>Result Table</PanelTitle>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>{response.table.columns.map((column) => <th key={column}>{column}</th>)}</tr>
          </thead>
          <tbody>
            {response.table.rows.map((row, index) => (
              <tr key={index}>
                {response.table?.columns.map((column) => <td key={column}>{String(row[column] ?? "")}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function ResultPanels({ response }: { response: AskResponse | null }) {
  if (!response) return null;
  return (
    <div className="results-grid">
      <div className="primary-results">
        {response.chart_spec ? <AnswerPanel response={response} /> : <RoutePanel response={response} />}

        {response.chart_spec ? <ChartPanel response={response} /> : <DetailPanel response={response} />}
      </div>
      <TablePanel response={response} />

      {response.sql && (
        <section className="panel">
          <PanelTitle icon={<FileText size={18} />}>SQL</PanelTitle>
          <pre>{response.sql}</pre>
        </section>
      )}

      {response.citations.length > 0 && (
        <section className="panel">
          <PanelTitle icon={<Link2 size={18} />}>Citations</PanelTitle>
          <div className="citation-list">
            {response.citations.map((citation) => (
              <article key={citation.ntsb_no} className="citation">
                <a href={citation.report_url} target="_blank" rel="noreferrer">{citation.ntsb_no}</a>
                <p>{citation.probable_cause || citation.matched_passage}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="panel">
        <PanelTitle icon={<History size={18} />}>Audit Trail</PanelTitle>
        <ol className="audit-list">
          {response.audit.map((event, index) => (
            <li key={`${event.step}-${index}`}>
              <strong>{event.step}</strong>
              <span>{event.detail}</span>
            </li>
          ))}
        </ol>
      </section>

      <section className="panel">
        <PanelTitle icon={<ShieldCheck size={18} />}>Limitations</PanelTitle>
        <ul className="limit-list">
          {response.limitations.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
    </div>
  );
}
