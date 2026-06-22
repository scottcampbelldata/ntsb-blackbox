# Security Model

Black Box AI should be hosted as a server-side application. The browser should never call model provider APIs directly.

## Bring Your Own Key

The BYOK model is:

1. User enters an OpenAI, Anthropic, or Gemini key in the UI.
2. The browser sends the key to the FastAPI backend over HTTPS.
3. The backend keeps the key only in memory for that session.
4. The key is never saved to disk.
5. The key is never written to logs.
6. Error messages are redacted before returning to the client.
7. The user can clear the key at any time.

`src/providers.py` contains the first utility layer for provider normalization, in-memory session key handling, and exact secret redaction.

## VPS Controls

Recommended VPS setup:

- HTTPS with a reverse proxy such as Caddy or Nginx.
- FastAPI running under a non-root user.
- Environment variables for server-owned config only, never user BYOK values.
- Postgres bound to localhost or a private network.
- Postgres app role with read-only permissions.
- Firewall open only for SSH, HTTP, and HTTPS.
- Systemd service with restart policy.
- Structured logs with request IDs.
- Explicit redaction filter for provider keys.

## SQL Safety

The app must not trust model-generated SQL. The required flow is:

1. Generate candidate SQL.
2. Parse and validate with `validate_sql`.
3. Execute only the returned validated SQL.
4. Use a read-only Postgres role.
5. Use a statement timeout and row limit.

The database permission layer is a second line of defense. The SQL guard is the first line.

## Chart Safety

The app must not let the model invent numbers inside chart specs.

The required flow is:

1. Execute validated SQL.
2. Build a real dataframe.
3. Ask the model for Vega-Lite JSON using only dataframe fields.
4. Validate the spec with `validate_vega_lite_spec`.
5. Render the chart from the dataframe plus the validated spec.

Specs containing `data`, `datasets`, `transform`, `params`, or `selection` are rejected.

