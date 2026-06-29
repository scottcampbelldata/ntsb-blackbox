import { useMemo, useState } from "react";
import { QuestionConsole } from "../components/QuestionConsole";
import { ProviderKeyPanel, modelOptions } from "../components/ProviderKeyPanel";
import { AnswerArticle } from "../components/AnswerArticle";
import { Disclosure, Eyebrow } from "../components/primitives";
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

export function AskTheRecord() {
  const sessionId = useMemo(getSessionId, []);
  const [provider, setProvider] = useState<Provider>("openai");
  const [model, setModel] = useState(modelOptions.openai[0]);
  const [apiKey, setApiKey] = useState("");
  const [question, setQuestion] = useState(
    "Which phases of flight have the highest fatal accident counts? Show a chart."
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
    <div className="mx-auto max-w-3xl px-5 py-12 sm:px-8 sm:py-16">
      <header className="mb-8">
        <Eyebrow>Natural-language query</Eyebrow>
        <h1 className="mt-3 font-display text-4xl font-medium text-ink sm:text-5xl">
          Ask the record
        </h1>
        <p className="lede mt-4">
          A question goes to a language model, which writes SQL or retrieves narratives — then the
          answer comes back with the query, the rows, its sources, and what it could not do.
        </p>
      </header>

      <QuestionConsole question={question} loading={loading} onQuestionChange={setQuestion} onSubmit={ask} />

      <div className="mt-4">
        <Disclosure label="Model & API key">
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
        </Disclosure>
      </div>

      {error && (
        <div className="mt-6 rounded-lg border border-danger/40 bg-surface p-4 text-sm text-danger">
          {error}
        </div>
      )}

      <AnswerArticle response={response} />
    </div>
  );
}
