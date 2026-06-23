import { Plane } from "lucide-react";
import { NavLink } from "react-router-dom";
import { ThemeToggle } from "./ThemeToggle";

export function Navbar() {
  return (
    <header className="navbar">
      <div className="brand">
        <Plane size={20} />
        <span className="brand-name">Black Box</span>
      </div>
      <nav className="nav-links">
        <NavLink to="/" end>Dashboard</NavLink>
        <NavLink to="/ask">Ask</NavLink>
        <NavLink to="/data">Data</NavLink>
      </nav>
      <ThemeToggle />
    </header>
  );
}
