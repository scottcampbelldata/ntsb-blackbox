import { NavLink } from "react-router-dom";
import { ThemeMenu } from "./ThemeMenu";
import { SiteBar } from "./SiteFrame";

export const CASE_STUDY = "https://scottcampbell.io/projects/black-box-ai/";
export const REPO = "https://github.com/scottcampbelldata/ntsb-blackbox";

const LINKS = [
  { to: "/", label: "Findings", end: true },
  { to: "/ask", label: "Ask the record", end: false },
  { to: "/data", label: "The data", end: false }
];

export function Masthead() {
  return (
    <>
      <SiteBar caseStudy={CASE_STUDY} repo={REPO} />
      <div className="app-strip">
        <div className="app-strip-inner">
          <NavLink to="/" className="app-name" aria-label="Black Box home">
            Black Box
          </NavLink>

          <nav className="order-3 -ml-2 flex w-full items-center gap-0 sm:order-2 sm:ml-auto sm:w-auto sm:gap-2" aria-label="Sections">
            {LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  [
                    "relative whitespace-nowrap px-2 py-3 text-base transition-colors sm:px-3",
                    isActive ? "text-ink" : "text-muted hover:text-ink"
                  ].join(" ")
                }
              >
                {({ isActive }) => (
                  <>
                    {link.label}
                    {isActive && (
                      <span aria-hidden="true" className="absolute inset-x-2 bottom-1.5 h-0.5 bg-accent sm:inset-x-3" />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>
          <div className="order-2 sm:order-3 sm:ml-1">
            <ThemeMenu />
          </div>
        </div>
      </div>
    </>
  );
}
