export type ChartRow = Record<string, string | number | null>;

export type ChartDescriptor = {
  kind: "bar" | "line";
  categoryKey: string;
  valueKey: string;
  title?: string;
  data: ChartRow[];
};

function markType(mark: unknown): string | null {
  if (typeof mark === "string") return mark;
  if (mark && typeof mark === "object" && "type" in mark) {
    const t = (mark as { type?: unknown }).type;
    return typeof t === "string" ? t : null;
  }
  return null;
}

function field(channel: unknown): string | null {
  if (channel && typeof channel === "object" && "field" in channel) {
    const f = (channel as { field?: unknown }).field;
    return typeof f === "string" ? f : null;
  }
  return null;
}

export function vegaLiteToRecharts(
  spec: Record<string, unknown> | null | undefined,
  rows: ChartRow[]
): ChartDescriptor | null {
  if (!spec) return null;

  const mark = markType(spec.mark);
  if (mark !== "bar" && mark !== "line") return null;

  const encoding = spec.encoding as Record<string, unknown> | undefined;
  if (!encoding) return null;

  const xField = field(encoding.x);
  const yField = field(encoding.y);
  if (!xField || !yField) return null;

  // Line: x is the category axis, y the value. Bar specs from the backend are
  // horizontal (x = quantitative value, y = nominal category), so the roles flip.
  const categoryKey = mark === "line" ? xField : yField;
  const valueKey = mark === "line" ? yField : xField;

  const title = typeof spec.title === "string" ? spec.title : undefined;

  return { kind: mark, categoryKey, valueKey, title, data: rows };
}
