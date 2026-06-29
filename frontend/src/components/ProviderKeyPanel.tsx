import { Trash2 } from "lucide-react";
import type { Provider } from "../types";

export const modelOptions: Record<Provider, string[]> = {
  openai: ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano"],
  anthropic: ["claude-sonnet-4-6", "claude-opus-4-8", "claude-haiku-4-5"],
  gemini: ["gemini-3.5-flash", "gemini-3.1-pro-preview", "gemini-3.1-flash-lite", "gemini-2.5-pro"]
};

type Props = {
  provider: Provider;
  model: string;
  apiKey: string;
  onProviderChange: (provider: Provider) => void;
  onModelChange: (model: string) => void;
  onApiKeyChange: (apiKey: string) => void;
  onClear: () => void;
};

const fieldClass =
  "mt-1 w-full rounded-md border border-rule bg-surface px-3 py-2 text-sm text-ink " +
  "transition-colors focus:border-accent focus:outline-none";
const labelClass = "block text-xs font-medium text-muted";

export function ProviderKeyPanel(props: Props) {
  return (
    <section className="grid gap-3 sm:grid-cols-2">
      <label className={labelClass}>
        Provider
        <select
          className={fieldClass}
          value={props.provider}
          onChange={(event) => props.onProviderChange(event.target.value as Provider)}
        >
          <option value="openai">OpenAI</option>
          <option value="anthropic">Claude</option>
          <option value="gemini">Gemini</option>
        </select>
      </label>
      <label className={labelClass}>
        Model
        <select
          className={fieldClass}
          value={props.model}
          onChange={(event) => props.onModelChange(event.target.value)}
        >
          {modelOptions[props.provider].map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      </label>
      <label className={`${labelClass} sm:col-span-2`}>
        API key
        <input
          className={`${fieldClass} data`}
          value={props.apiKey}
          onChange={(event) => props.onApiKeyChange(event.target.value)}
          placeholder="Stored for this server session only"
          type="password"
        />
      </label>
      <button
        className="inline-flex items-center gap-1.5 justify-self-start text-xs text-muted transition-colors hover:text-danger"
        onClick={props.onClear}
        type="button"
        title="Clear session key"
      >
        <Trash2 size={14} aria-hidden="true" />
        Clear key
      </button>
    </section>
  );
}
