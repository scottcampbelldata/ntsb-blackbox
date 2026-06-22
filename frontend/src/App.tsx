import { useMemo, useState } from "react";
import { Plane } from "lucide-react";
import { AskPanel } from "./components/AskPanel";
import { ProviderKeyPanel, modelOptions } from "./components/ProviderKeyPanel";
import { ResultPanels } from "./components/ResultPanels";
import type { AskResponse, Provider } from "./types";
import "./styles.css";

const sessionKey = "blackbox-session-id";

// In production (Cloudflare Pages) this is set to the backend subdomain.
// Left empty in local dev so requests stay relative and hit the Vite proxy.
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

function getSessionId() {
  const existing = window.localStorage.getItem(sessionKey);
  if (existing) return existing;
  const created = crypto.randomUUID();
  window.localStorage.setItem(sessionKey, created);
  return created;
}

export default function App() {
  const sessionId = useMemo(getSessionId, []);
  const [provider, setProvider] = useState<Provider>("openai");
  const [model, setModel] = useState(modelOptions.openai[0]);
  const [apiKey, setApiKey] = useState("");
  const [question, setQuestion] = useState("Which phases of flight have the highest fatal accident counts, and show it as a chart?");
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask() {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const res = await fetch(`${API_BASE}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Session-ID": sessionId },
        body: JSON.stringify({
          question,
          provider,
          model,
          api_key: apiKey || null,
          chart_preference: "auto",
          session_id: sessionId
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request failed");
      setResponse(data);
      setApiKey("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function clearKey() {
    await fetch(`${API_BASE}/api/keys/clear`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Session-ID": sessionId },
      body: JSON.stringify({ provider, session_id: sessionId })
    });
    setApiKey("");
  }

  return (
    <main>
      <header className="topbar">
        <div className="brand">
          <Plane size={22} />
          <div>
            <h1>Black Box AI</h1>
            <p>Natural-language aviation safety analytics over NTSB final reports</p>
          </div>
        </div>
        <details className="provider-menu">
          <summary>Model Key</summary>
          <ProviderKeyPanel
            provider={provider}
            model={model}
            apiKey={apiKey}
            onProviderChange={(nextProvider) => {
              setProvider(nextProvider);
              setModel(modelOptions[nextProvider][0]);
            }}
            onModelChange={setModel}
            onApiKeyChange={setApiKey}
            onClear={clearKey}
          />
        </details>
      </header>

      <div className="workspace">
        <section className="main-column">
          <AskPanel question={question} loading={loading} onQuestionChange={setQuestion} onSubmit={ask} />
          {error && <div className="error">{error}</div>}
          <ResultPanels response={response} />
        </section>
      </div>
    </main>
  );
}
