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
    <div className="tabs">
      <div className="tablist" role="tablist">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={index === active}
            className={`tab${index === active ? " tab-active" : ""}`}
            onClick={() => setActive(index)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tab-panel" role="tabpanel">
        {current.content}
      </div>
    </div>
  );
}
