import { CornerDownLeft, Send } from "lucide-react";
import { Eyebrow } from "./primitives";

type Props = {
  question: string;
  loading: boolean;
  onQuestionChange: (question: string) => void;
  onSubmit: () => void;
};

const EXAMPLES = [
  "Which phases of flight have the highest fatal accident counts? Show a chart.",
  "Why do pilots lose control in icing conditions?",
  "Are landing accidents more common than enroute, but less often fatal?",
  "Show accidents in Ohio by year."
];

export function QuestionConsole({ question, loading, onQuestionChange, onSubmit }: Props) {
  const canSubmit = !loading && question.trim().length >= 3;

  function onKeyDown(event: React.KeyboardEvent) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && canSubmit) {
      event.preventDefault();
      onSubmit();
    }
  }

  return (
    <section>
      <div className="rounded-xl border border-rule bg-surface p-2 shadow-card focus-within:border-accent">
        <textarea
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask a question of 7,462 accident reports…"
          rows={3}
          className="w-full resize-none bg-transparent px-3 py-2 font-display text-lg leading-snug text-ink placeholder:text-muted/70 focus:outline-none"
        />
        <div className="flex items-center justify-between gap-3 px-3 pb-1">
          <span className="hidden items-center gap-1 text-xs text-muted sm:inline-flex">
            <CornerDownLeft size={12} aria-hidden="true" />
            <span className="data">⌘/Ctrl + Enter</span>
          </span>
          <button
            type="button"
            onClick={onSubmit}
            disabled={!canSubmit}
            className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-accent-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Send size={15} aria-hidden="true" />
            {loading ? "Reading the record…" : "Ask"}
          </button>
        </div>
      </div>

      <div className="mt-4">
        <Eyebrow>Try</Eyebrow>
        <div className="mt-2 flex flex-wrap gap-2">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => onQuestionChange(example)}
              className="rounded-full border border-rule bg-surface px-3 py-1.5 text-left text-xs text-ink-soft transition-colors hover:border-accent hover:text-ink"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
