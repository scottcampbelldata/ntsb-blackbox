import { useMemo, useState } from "react";
import { AskPanel } from "../components/AskPanel";
import { ProviderKeyPanel, modelOptions } from "../components/ProviderKeyPanel";
import { ResultPanels } from "../components/ResultPanels";
import type { AskResponse, Provider } from "../types";
import { ask as askApi, clearKey as clearKeyApi } from "../lib/api";

const sessionKey = "blackbox-session-id";

function getSessionId() {
  const existing = window.localStorage.getItem(sessionKey);
  if (existing) return existing;
  const created = crypto.randomUUID();
  window.localStorage.setItem(sessionKey, created);
  return created;
}

export function Ask() {
  const sessionId = useMemo(getSessionId, []);
  const [provider, setProvider] = useState<Provider>("openai");
  const [model, setModel] = useState(modelOptions.openai[0]);
  const [apiKey, setApiKey] = useState("");
  const [question, setQuestion] = useState(
    "Which phases of flight have the highest fatal accident counts, and show it as a chart?"
  );
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask() {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const data = await askApi({ question, provider, model, apiKey: apiKey || null, sessionId });
      setResponse(data);
      setApiKey("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function clearKey() {
    await clearKeyApi({ provider, sessionId });
    setApiKey("");
  }

  return (
    <div className="workspace">
      <section className="main-column">
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
        <AskPanel question={question} loading={loading} onQuestionChange={setQuestion} onSubmit={ask} />
        {error && <div className="error">{error}</div>}
        <ResultPanels response={response} />
      </section>
    </div>
  );
}
