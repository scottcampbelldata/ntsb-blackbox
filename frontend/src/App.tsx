import { Route, Routes } from "react-router-dom";
import { Masthead, CASE_STUDY } from "./components/Masthead";
import { ConsultFooter } from "./components/SiteFrame";
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
      <div className="mx-auto mt-14 w-full max-w-6xl px-5 sm:px-8">
        <div className="border-t border-rule pt-6">
          <p className="measure text-base text-muted">
            Black Box reads the public record: US NTSB aviation accident final reports. The name is
            ironic: a flight recorder is a black box, but here every figure shows the SQL that
            produced it and every answer cites its source.
          </p>
          <p className="mt-2 text-sm text-muted">
            Source: NTSB, public domain. Not affiliated with the NTSB.
          </p>
        </div>
      </div>
      <ConsultFooter caseStudy={CASE_STUDY} />
    </div>
  );
}
