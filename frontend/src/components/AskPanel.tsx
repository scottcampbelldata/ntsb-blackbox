import { Send, Sparkles } from "lucide-react";

type Props = {
  question: string;
  loading: boolean;
  onQuestionChange: (question: string) => void;
  onSubmit: () => void;
};

const examples = [
  "Which phases of flight have the highest fatal accident counts, and show it as a chart?",
  "Why do pilots lose control in icing conditions?",
  "Are landing accidents more common than enroute accidents, but are they less fatal?",
  "Show accidents in Ohio by year."
];

export function AskPanel({ question, loading, onQuestionChange, onSubmit }: Props) {
  return (
    <section className="ask-panel">
      <div className="ask-row">
        <textarea
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          placeholder="Ask about the loaded NTSB accident corpus"
          rows={2}
        />
        <button className="primary-button" onClick={onSubmit} disabled={loading || question.trim().length < 3} type="button">
          <Send size={18} />
          {loading ? "Asking" : "Ask"}
        </button>
      </div>
      <div className="examples">
        <Sparkles size={16} />
        <select value="" onChange={(event) => event.target.value && onQuestionChange(event.target.value)}>
          <option value="">Choose an example</option>
          {examples.map((example) => (
            <option key={example} value={example}>
              {example}
            </option>
          ))}
        </select>
      </div>
    </section>
  );
}
