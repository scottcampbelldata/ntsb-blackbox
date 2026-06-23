import { Route, Routes } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { Dashboard } from "./pages/Dashboard";
import { Ask } from "./pages/Ask";
import { Data } from "./pages/Data";
import "./theme/theme.css";
import "./styles.css";

export default function App() {
  return (
    <main>
      <Navbar />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/ask" element={<Ask />} />
        <Route path="/data" element={<Data />} />
      </Routes>
    </main>
  );
}
