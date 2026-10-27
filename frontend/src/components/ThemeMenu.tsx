import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme, type ThemeMode } from "../theme/useTheme";

const OPTIONS: { mode: ThemeMode; label: string; Icon: typeof Sun }[] = [
  { mode: "system", label: "System", Icon: Monitor },
  { mode: "light", label: "Light", Icon: Sun },
  { mode: "dark", label: "Dark", Icon: Moon }
];

export function ThemeMenu() {
  const { mode, setMode } = useTheme();

  return (
    <div
      role="group"
      aria-label="Color theme"
      className="inline-flex items-center gap-0.5 rounded-md border border-rule bg-surface-sunken p-0.5"
    >
      {OPTIONS.map(({ mode: value, label, Icon }) => {
        const active = mode === value;
        return (
          <button
            key={value}
            type="button"
            aria-pressed={active}
            title={`${label} theme`}
            onClick={() => setMode(value)}
            className={[
              "grid h-8 w-8 place-items-center rounded-md transition-colors",
              active
                ? "bg-surface text-accent"
                : "text-muted hover:text-ink"
            ].join(" ")}
          >
            <Icon size={15} strokeWidth={2} aria-hidden="true" />
            <span className="sr-only">{label}</span>
          </button>
        );
      })}
    </div>
  );
}
