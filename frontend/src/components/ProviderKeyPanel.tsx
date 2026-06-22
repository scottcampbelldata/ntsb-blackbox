import { KeyRound, Trash2 } from "lucide-react";
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

export function ProviderKeyPanel(props: Props) {
  return (
    <section className="panel key-panel">
      <div className="panel-title">
        <KeyRound size={18} />
        <span>Model Key</span>
      </div>
      <div className="form-grid">
        <label>
          Provider
          <select value={props.provider} onChange={(event) => props.onProviderChange(event.target.value as Provider)}>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Claude</option>
            <option value="gemini">Gemini</option>
          </select>
        </label>
        <label>
          Model
          <select value={props.model} onChange={(event) => props.onModelChange(event.target.value)}>
            {modelOptions[props.provider].map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label>
        API key
        <input
          value={props.apiKey}
          onChange={(event) => props.onApiKeyChange(event.target.value)}
          placeholder="Used for this server session only"
          type="password"
        />
      </label>
      <button className="ghost-button" onClick={props.onClear} type="button" title="Clear session key">
        <Trash2 size={16} />
        Clear
      </button>
    </section>
  );
}
