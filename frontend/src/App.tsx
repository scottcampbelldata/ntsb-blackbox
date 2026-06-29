import { Route, Routes } from "react-router-dom";
import { Masthead } from "./components/Masthead";
import { Findings } from "./pages/Findings";
import { AskTheRecord } from "./pages/AskTheRecord";
import { TheData } from "./pages/TheData";

export default function App() {
  return (
    <div className="flex min-h-dvh flex-col">
      <Masthead />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Findings />} />
          <Route path="/ask" element={<AskTheRecord />} />
          <Route path="/data" element={<TheData />} />
        </Routes>
      </main>
      <footer className="border-t border-rule">
        <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
          <p className="measure text-sm text-muted">
            Black Box reads the public record: US NTSB aviation accident final reports. The name is
            ironic — a flight recorder is a black box, but here every figure shows the SQL that
            produced it and every answer cites its source.
          </p>
          <p className="eyebrow mt-3">NTSB · public domain · not affiliated with the NTSB</p>
        </div>
      </footer>
    </div>
  );
}
