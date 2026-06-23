import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { vegaLiteToRecharts, type ChartRow } from "../lib/vegaLiteToRecharts";

const SERIES = "var(--chart-series, #1f6f78)";

export function ChartView({
  spec,
  rows
}: {
  spec: Record<string, unknown> | null | undefined;
  rows: ChartRow[];
}) {
  const descriptor = vegaLiteToRecharts(spec, rows);
  if (!descriptor) return null;

  const { kind, categoryKey, valueKey, title, data } = descriptor;

  return (
    <figure className="chart-view">
      {title && <figcaption className="chart-title">{title}</figcaption>}
      <div className="chart-host">
        <ResponsiveContainer width="100%" height={340}>
          {kind === "line" ? (
            <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--rule, #e3e8eb)" />
              <XAxis dataKey={categoryKey} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey={valueKey} stroke={SERIES} strokeWidth={2} dot={false} />
            </LineChart>
          ) : (
            <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--rule, #e3e8eb)" />
              <XAxis type="number" dataKey={valueKey} />
              <YAxis type="category" dataKey={categoryKey} width={140} />
              <Tooltip />
              <Bar dataKey={valueKey} fill={SERIES} radius={[0, 2, 2, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </figure>
  );
}
