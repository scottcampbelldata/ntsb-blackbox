import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { vegaLiteToRecharts, type ChartRow } from "../lib/vegaLiteToRecharts";

const AXIS_TICK = { fontFamily: "var(--font-mono)", fontSize: 11, fill: "var(--muted)" };

function fmt(value: unknown): string {
  return typeof value === "number" ? value.toLocaleString("en-US") : String(value ?? "");
}

function ChartTooltip({
  active,
  payload,
  label,
  categoryKey
}: {
  active?: boolean;
  payload?: { value: number; name: string }[];
  label?: string | number;
  categoryKey: string;
}) {
  if (!active || !payload?.length) return null;
  const head = categoryKey === "year" ? label : payload[0]?.name ?? label;
  return (
    <div className="rounded-md border border-rule-strong bg-surface px-3 py-2 shadow-card">
      <p className="eyebrow mb-0.5">{String(head)}</p>
      <p className="data text-sm font-medium text-ink">{fmt(payload[0]?.value)}</p>
    </div>
  );
}

export function ChartView({
  spec,
  rows,
  height = 320
}: {
  spec: Record<string, unknown> | null | undefined;
  rows: ChartRow[];
  height?: number;
}) {
  const descriptor = vegaLiteToRecharts(spec, rows);
  if (!descriptor) return null;
  const { kind, categoryKey, valueKey, data } = descriptor;

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        {kind === "line" ? (
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
            <CartesianGrid vertical={false} stroke="var(--rule)" strokeDasharray="2 4" />
            <XAxis dataKey={categoryKey} tick={AXIS_TICK} tickLine={false} stroke="var(--rule-strong)" />
            <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} width={40} />
            <Tooltip
              cursor={{ stroke: "var(--accent)", strokeWidth: 1, strokeDasharray: "3 3" }}
              content={<ChartTooltip categoryKey={categoryKey} />}
            />
            <Line
              type="monotone"
              dataKey={valueKey}
              stroke="var(--accent)"
              strokeWidth={2.25}
              dot={{ r: 2.5, fill: "var(--accent)", strokeWidth: 0 }}
              activeDot={{ r: 4, fill: "var(--accent)", strokeWidth: 0 }}
            />
          </LineChart>
        ) : (
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 4 }}>
            <CartesianGrid horizontal={false} stroke="var(--rule)" strokeDasharray="2 4" />
            <XAxis type="number" dataKey={valueKey} tick={AXIS_TICK} tickLine={false} axisLine={false} />
            <YAxis
              type="category"
              dataKey={categoryKey}
              tick={AXIS_TICK}
              tickLine={false}
              axisLine={false}
              width={132}
            />
            <Tooltip
              cursor={{ fill: "var(--accent-wash)" }}
              content={<ChartTooltip categoryKey={categoryKey} />}
            />
            <Bar dataKey={valueKey} radius={[0, 3, 3, 0]} maxBarSize={28}>
              {/* Lead row reads in signal orange; the rest recede to instrument cyan. */}
              {data.map((_, index) => (
                <Cell key={index} fill={index === 0 ? "var(--accent)" : "var(--cyan)"} />
              ))}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
