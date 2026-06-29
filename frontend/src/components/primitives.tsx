import { ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

/** Small mono kicker. Use it for real taxonomy (phase, weather, report no.). */
export function Eyebrow({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <p className={`eyebrow ${className}`}>{children}</p>;
}

// The signature device: a flight-data trace standing in for a section rule.
// A recorder captures parameters as a jagged track over time; this echoes it,
// ending in the orange "current sample" dot. Decorative, so hidden from AT.
const TRACE =
  "0,21 52,18 96,25 138,11 184,23 232,8 286,27 338,15 392,29 446,13 " +
  "502,24 560,9 624,26 690,17 752,28 812,12 874,22 938,16 1000,20";

export function TraceRule({ className = "" }: { className?: string }) {
  return (
    <div role="presentation" className={`flex items-center gap-2 ${className}`}>
      <svg
        className="h-3 w-full flex-1 text-rule-strong"
        viewBox="0 0 1000 40"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <polyline
          points={TRACE}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
    </div>
  );
}

/** Pulsing placeholder used while data loads. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-surface-sunken ${className}`} aria-hidden="true" />;
}

// The transparency motif made concrete: anything the system did is one click
// from view. Native <details> for free keyboard + AT support.
export function Disclosure({
  label,
  children,
  defaultOpen = false
}: {
  label: string;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  return (
    <details className="group border-t border-rule pt-3" open={defaultOpen}>
      <summary className="flex cursor-pointer list-none items-center gap-1.5 text-muted transition-colors hover:text-ink [&::-webkit-details-marker]:hidden">
        <ChevronRight
          size={13}
          className="shrink-0 transition-transform duration-200 group-open:rotate-90"
          aria-hidden="true"
        />
        <span className="eyebrow">{label}</span>
      </summary>
      <div className="mt-3">{children}</div>
    </details>
  );
}
