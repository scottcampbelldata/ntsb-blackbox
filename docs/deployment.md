# VPS Deployment

This is the intended production shape:

```text
Internet
  -> Caddy or Nginx HTTPS reverse proxy
  -> React static frontend
  -> FastAPI backend on localhost:8000
  -> Postgres on localhost/private network
```

## Postgres

Create a database and roles:

```sql
CREATE DATABASE ntsb_blackbox;
CREATE USER <loader-db-role> WITH PASSWORD '<loader-db-password>';
CREATE USER <app-db-role> WITH PASSWORD '<app-db-password>';
GRANT CONNECT ON DATABASE ntsb_blackbox TO <loader-db-role>, <app-db-role>;
```

Load data with a migration/owner role:

```bash
python scripts/load_postgres.py \
  --database-url "postgresql://<loader-db-role>:<loader-db-password>@localhost:5432/ntsb_blackbox"
```

Then grant read-only app access:

```sql
GRANT USAGE ON SCHEMA public TO <app-db-role>;
GRANT SELECT ON accidents, ingest_runs, source_records TO <app-db-role>;
```

Set the app runtime URL to the read-only role:

```bash
export DATABASE_URL="postgresql://<app-db-role>:<app-db-password>@localhost:5432/ntsb_blackbox"
```

## Backend

```bash
python -m pip install -r requirements.txt
uvicorn backend.app.main:app --host localhost --port 8000
```

Recommended environment variables:

```bash
export DATABASE_URL="postgresql://<app-db-role>:<app-db-password>@localhost:5432/ntsb_blackbox"
export ALLOWED_ORIGINS="https://your-domain.com"
export QUERY_TIMEOUT_MS="5000"
export MAX_QUERY_ROWS="500"
```

## Frontend

```bash
cd frontend
npm install
npm run build
```

Serve `frontend/dist` with the reverse proxy, and proxy `/api/*` plus `/health` to FastAPI.

## Data Updates

The app has a production update path for refreshed NTSB exports:

- `<loader-db-role>` owns writes to Postgres.
- `<app-db-role>` is read-only and serves the web app.
- `source_records` stores one content hash per NTSB report.
- `ingest_runs` stores every update attempt, row counts, status, and errors.
- Changed reports update Postgres and narrative files idempotently.
- Retrieval caches are invalidated and the vector index is rebuilt only when records change.

Run a dry run first:

```bash
python scripts/update_ntsb.py \
  --database-url "postgresql://<loader-db-role>:<loader-db-password>@localhost:5432/ntsb_blackbox" \
  --source-csv /opt/ntsb-blackbox/data/raw/latest_ntsb_reports.csv \
  --dry-run
```

Then run the real update:

```bash
python scripts/update_ntsb.py \
  --database-url "postgresql://<loader-db-role>:<loader-db-password>@localhost:5432/ntsb_blackbox" \
  --source-csv /opt/ntsb-blackbox/data/raw/latest_ntsb_reports.csv
```

For a hosted CSV snapshot, use `--source-url` instead of `--source-csv`:

```bash
python scripts/update_ntsb.py \
  --database-url "postgresql://<loader-db-role>:<loader-db-password>@localhost:5432/ntsb_blackbox" \
  --source-url "https://example.org/latest_ntsb_reports.csv"
```

`/health` reports database type, accident count, tracking-table readiness, and the latest ingest run. After a scheduled update, check:

```bash
curl https://your-domain.com/health
```

## Systemd Update Timer

Use a timer on the VPS when the source CSV/export is refreshed on a predictable cadence.

`/etc/systemd/system/blackbox-update.service`:

```ini
[Unit]
Description=Update Black Box AI NTSB data
After=network.target postgresql.service

[Service]
Type=oneshot
User=<service-account>
WorkingDirectory=/opt/ntsb-blackbox
Environment=DATABASE_URL=postgresql://<loader-db-role>:<loader-db-password>@localhost:5432/ntsb_blackbox
ExecStart=/opt/ntsb-blackbox/.venv/bin/python scripts/update_ntsb.py --source-csv /opt/ntsb-blackbox/data/raw/latest_ntsb_reports.csv
```

`/etc/systemd/system/blackbox-update.timer`:

```ini
[Unit]
Description=Run Black Box AI NTSB data update daily

[Timer]
OnCalendar=03:30
Persistent=true

[Install]
WantedBy=timers.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now blackbox-update.timer
systemctl list-timers blackbox-update.timer
```

## Systemd Backend Service

```ini
[Unit]
Description=Black Box AI FastAPI
After=network.target

[Service]
User=<service-account>
WorkingDirectory=/opt/ntsb-blackbox
Environment=DATABASE_URL=postgresql://<app-db-role>:<app-db-password>@localhost:5432/ntsb_blackbox
Environment=ALLOWED_ORIGINS=https://your-domain.com
ExecStart=/opt/ntsb-blackbox/.venv/bin/uvicorn backend.app.main:app --host localhost --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
