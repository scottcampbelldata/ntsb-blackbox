import { NavLink } from "react-router-dom";
import { ThemeMenu } from "./ThemeMenu";

const LINKS = [
  { to: "/", label: "Findings", end: true },
  { to: "/ask", label: "Ask the record", end: false },
  { to: "/data", label: "The data", end: false }
];

export function Masthead() {
  return (
    <header className="sticky top-0 z-30 border-b border-rule bg-paper/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5 sm:px-8">
        <NavLink to="/" className="group flex items-center gap-2.5" aria-label="Black Box — home">
          {/* The recorder: flight data recorders are painted this orange. */}
          <span
            aria-hidden="true"
            className="h-3.5 w-3.5 shrink-0 rounded-[2px] bg-accent shadow-[0_0_0_3px_var(--accent-wash)]"
          />
          <span className="font-display text-xl leading-none tracking-tight text-ink">
            Black Box
          </span>
        </NavLink>

        <nav className="flex items-center gap-1 sm:gap-2" aria-label="Sections">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                [
                  "relative rounded-md px-2.5 py-1.5 text-sm transition-colors sm:px-3",
                  isActive ? "text-ink" : "text-muted hover:text-ink"
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  <span className="hidden sm:inline">{link.label}</span>
                  <span className="sm:hidden">{link.label.split(" ")[0]}</span>
                  {isActive && (
                    <span
                      aria-hidden="true"
                      className="absolute inset-x-2.5 -bottom-px h-0.5 rounded-full bg-accent"
                    />
                  )}
                </>
              )}
            </NavLink>
          ))}
          <div className="ml-1 sm:ml-3">
            <ThemeMenu />
          </div>
        </nav>
      </div>
    </header>
  );
}
