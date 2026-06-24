import { ChartView } from "./ChartView";
import { Tabs, type TabItem } from "./Tabs";
import type { AskResponse } from "../types";

function AnswerHeader({ response }: { response: AskResponse }) {
  return (
    <section className="answer-header">
      <p className="answer-text">{response.answer}</p>
      <div className="answer-meta">
        <span className="route-badge">{response.route.route.toUpperCase()}</span>
        <span className="confidence tabular">{Math.round(response.confidence * 100)}% confidence</span>
      </div>
    </section>
  );
}

function ResultTable({ table }: { table: NonNullable<AskResponse["table"]> }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>{table.columns.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {table.rows.map((row, i) => (
            <tr key={i}>{table.columns.map((c) => <td key={c}>{String(row[c] ?? "")}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Citations({ citations }: { citations: AskResponse["citations"] }) {
  return (
    <div className="citation-list">
      {citations.map((c) => (
        <article key={c.ntsb_no} className="citation">
          {c.report_url ? (
            <a href={c.report_url} target="_blank" rel="noreferrer">{c.ntsb_no}</a>
          ) : (
            <span className="citation-id">{c.ntsb_no}</span>
          )}
          <p>{c.probable_cause || c.matched_passage}</p>
        </article>
      ))}
    </div>
  );
}

export function ResultPanels({ response }: { response: AskResponse | null }) {
  if (!response) return null;

  const tabs: TabItem[] = [];
  if (response.sql) {
    tabs.push({ id: "sql", label: "SQL", content: <pre>{response.sql}</pre> });
  }
  if (response.table) {
    tabs.push({ id: "table", label: "Table", content: <ResultTable table={response.table} /> });
  }
  if (response.citations.length > 0) {
    tabs.push({
      id: "citations",
      label: `Citations (${response.citations.length})`,
      content: <Citations citations={response.citations} />
    });
  }
  tabs.push({
    id: "audit",
    label: "Audit",
    content: (
      <ol className="audit-list">
        {response.audit.map((e, i) => (
          <li key={`${e.step}-${i}`}>
            <strong>{e.step}</strong>
            <span>{e.detail}</span>
          </li>
        ))}
      </ol>
    )
  });

  return (
    <div className="result">
      <AnswerHeader response={response} />
      {response.chart_spec && response.table && (
        <section className="result-chart">
          <ChartView spec={response.chart_spec} rows={response.table.rows} />
        </section>
      )}
      <Tabs tabs={tabs} />
      <section className="limitations">
        <h4>Limitations</h4>
        {response.limitations.length > 0 ? (
          <ul className="limit-list">
            {response.limitations.map((item) => <li key={item}>{item}</li>)}
          </ul>
        ) : (
          <p className="no-limitations">None reported.</p>
        )}
      </section>
    </div>
  );
}
