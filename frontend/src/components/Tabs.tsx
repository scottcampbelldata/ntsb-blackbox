import { useEffect, useState } from "react";

export type TabItem = { id: string; label: string; content: React.ReactNode };

export function Tabs({ tabs }: { tabs: TabItem[] }) {
  const [active, setActive] = useState(0);
  useEffect(() => {
    if (active >= tabs.length && tabs.length > 0) setActive(0);
  }, [tabs.length]);
  if (tabs.length === 0) return null;
  const current = tabs[Math.min(active, tabs.length - 1)];

  return (
    <div>
      <div className="flex flex-wrap gap-1 border-b border-rule" role="tablist">
        {tabs.map((tab, index) => {
          const isActive = index === active;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={[
                "-mb-px border-b-2 px-3 py-2 font-mono text-xs uppercase tracking-wider transition-colors",
                isActive
                  ? "border-accent text-ink"
                  : "border-transparent text-muted hover:text-ink"
              ].join(" ")}
              onClick={() => setActive(index)}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      <div className="pt-4" role="tabpanel">
        {current.content}
      </div>
    </div>
  );
}
