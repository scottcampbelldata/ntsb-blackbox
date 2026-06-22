# Black Box AI Architecture

Black Box AI is moving from a no-LLM public demo toward a VPS-hosted natural-language analytics system over the NTSB accident corpus.

The current repo remains useful as the data and retrieval core:

- `src/ingest.py` builds the structured accident table and narrative files.
- `src/search.py`, `src/bm25_search.py`, and `src/hybrid_search.py` provide narrative retrieval.
- `src/sql_tool.py` preserves trusted prebuilt analyses for the public demo.
- `src/router.py` provides the transparent baseline router.

The production target is:

```text
Browser UI
  -> FastAPI backend on VPS
  -> provider adapter for OpenAI, Anthropic, or Gemini
  -> guarded SQL planner
  -> read-only Postgres role
  -> retrieval over narrative index
  -> validated Vega-Lite chart spec
  -> answer, table, chart, citations, SQL, audit trail
```

## Request Flow

1. User asks a plain-English question about the NTSB accident corpus.
2. Backend routes the question to SQL, retrieval, charting, or a combined path.
3. For analytical questions, an LLM generates candidate Postgres SQL from the schema catalog.
4. `src/sql_guard.py` parses the SQL as Postgres and rejects unsafe statements.
5. The backend executes accepted SQL with a read-only Postgres role, statement timeout, and row limit.
6. If a chart is requested, the model generates Vega-Lite JSON from the real dataframe schema.
7. `src/chart_validator.py` rejects specs with embedded data, transforms, missing fields, or unsupported marks.
8. The answer composer returns the visible SQL, result table, chart spec, chart, citations, route decision, and limitations.

## Postgres Deployment Notes

Use Postgres as the server database and keep SQLite as a local/demo compatibility path.

Recommended production controls:

- Separate database role for the app.
- Grant only `SELECT` on the approved analytics schema/table.
- Set `statement_timeout`.
- Set `idle_in_transaction_session_timeout`.
- Route all generated SQL through `validate_sql`.
- Execute generated SQL only through parameterless read-only transactions.
- Log query fingerprints and validation outcomes, not API keys.

## Core Contracts

Generated SQL must be:

- One Postgres `SELECT`.
- Against the approved `accidents` table.
- Limited to cataloged columns.
- Limited to approved functions.
- Bounded by `LIMIT`.

Generated charts must be:

- Vega-Lite JSON.
- Free of embedded model-invented data.
- Bound only to fields returned by the executed query.
- Validated before rendering.

