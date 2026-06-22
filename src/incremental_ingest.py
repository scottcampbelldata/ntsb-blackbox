import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

from build_index import build as rebuild_vector_index
from ingest import KEY_COL, TEXT_COL, to_snake
from paths import BM25_CACHE_PATH, DB_PATH, DOCS_DIR, PROJECT_ROOT
from schema_catalog import COLUMNS, TABLE_NAME


INGEST_RUNS_TABLE = "ingest_runs"
SOURCE_RECORDS_TABLE = "source_records"
CSV_SEP = ";"
CSV_ENCODING = "utf-8"


@dataclass(frozen=True)
class UpdateStats:
    records_seen: int
    records_inserted: int
    records_updated: int
    records_unchanged: int
    index_rebuilt: bool
    dry_run: bool


def stable_record_hash(row, columns):
    payload = {column: _json_safe(row.get(column)) for column in columns}
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_source_csv(path):
    df = pd.read_csv(path, sep=CSV_SEP, encoding=CSV_ENCODING, low_memory=False)
    df.columns = [to_snake(column) for column in df.columns]
    if KEY_COL not in df.columns:
        raise ValueError(f"Expected key column {KEY_COL!r}; got {df.columns.tolist()}")
    if TEXT_COL not in df.columns:
        raise ValueError(f"Expected narrative column {TEXT_COL!r}; got {df.columns.tolist()}")
    for column in df.columns:
        if column.endswith("_count"):
            df[column] = pd.to_numeric(df[column], errors="coerce")
    if "event_date" in df.columns:
        df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce", utc=True)
        df["event_year"] = df["event_date"].dt.year
        df["event_date"] = df["event_date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def download_source(source_url, target_dir):
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = source_url.rstrip("/").split("/")[-1] or "ntsb_source.csv"
    target = target_dir / filename
    urlretrieve(source_url, target)
    return target


class IncrementalUpdater:
    def __init__(self, database_url=None, docs_dir=DOCS_DIR):
        self.database_url = database_url or f"sqlite:///{DB_PATH}"
        self.docs_dir = Path(docs_dir)

    def update_from_csv(self, source_csv, *, source_name=None, dry_run=False, rebuild_index=True):
        source_csv = Path(source_csv)
        source_name = source_name or str(_display_path(source_csv))
        df = load_source_csv(source_csv)
        structured_columns = [column.name for column in COLUMNS if column.name in df.columns]
        hash_columns = sorted(set(structured_columns + [TEXT_COL]))
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as con:
            self._ensure_tracking_tables(con)
            run_id = self._start_run(con, source_name, now, dry_run)
            inserted = updated = unchanged = 0
            changed_doc_ids = []
            try:
                for row in df.to_dict(orient="records"):
                    ntsb_no = str(row.get(KEY_COL) or "").strip()
                    if not ntsb_no:
                        continue
                    content_hash = stable_record_hash(row, hash_columns)
                    existing = self._source_record(con, ntsb_no)
                    if existing and existing["content_hash"] == content_hash:
                        unchanged += 1
                        continue
                    if existing:
                        updated += 1
                    else:
                        inserted += 1
                    changed_doc_ids.append(ntsb_no)

                    if dry_run:
                        continue

                    self._upsert_accident(con, row, structured_columns)
                    self._write_doc(ntsb_no, row.get(TEXT_COL))
                    self._upsert_source_record(
                        con,
                        ntsb_no=ntsb_no,
                        event_id=row.get("event_i_d"),
                        report_url=row.get("report_url"),
                        newest_report_url=row.get("report_url"),
                        source_updated_at=row.get("original_published_date") or row.get("most_recent_report_type"),
                        content_hash=content_hash,
                        ingested_at=now,
                    )

                index_rebuilt = False
                if changed_doc_ids and rebuild_index and not dry_run:
                    self._invalidate_bm25_cache()
                    rebuild_vector_index()
                    index_rebuilt = True

                stats = UpdateStats(
                    records_seen=len(df),
                    records_inserted=inserted,
                    records_updated=updated,
                    records_unchanged=unchanged,
                    index_rebuilt=index_rebuilt,
                    dry_run=dry_run,
                )
                self._finish_run(con, run_id, "ok", stats=stats)
                self._commit(con)
                return stats
            except Exception as exc:
                self._rollback(con)
                self._finish_run(con, run_id, "error", error=str(exc))
                self._commit(con)
                raise

    @contextmanager
    def _connect(self):
        if self.database_url.startswith("sqlite:///"):
            path = Path(self.database_url.removeprefix("sqlite:///"))
            path.parent.mkdir(parents=True, exist_ok=True)
            con = sqlite3.connect(path)
            con.row_factory = sqlite3.Row
            try:
                yield con
            finally:
                con.close()
            return

        if self.database_url.startswith(("postgresql://", "postgres://")):
            import psycopg
            from psycopg.rows import dict_row

            url = self.database_url
            if url.startswith("postgres://"):
                url = "postgresql://" + url.removeprefix("postgres://")
            with psycopg.connect(url, row_factory=dict_row) as con:
                yield PostgresConnection(con)
            return

        raise ValueError(f"Unsupported database URL: {self.database_url}")

    def _commit(self, con):
        con.commit()

    def _rollback(self, con):
        con.rollback()

    def _execute(self, con, sql, params=()):
        return con.execute(sql, params)

    def _ensure_tracking_tables(self, con):
        self._ensure_accidents_table(con)
        if isinstance(con, PostgresConnection):
            con.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {INGEST_RUNS_TABLE} (
                  id bigserial PRIMARY KEY,
                  started_at timestamptz NOT NULL,
                  finished_at timestamptz,
                  source_name text,
                  records_seen integer DEFAULT 0,
                  records_inserted integer DEFAULT 0,
                  records_updated integer DEFAULT 0,
                  records_unchanged integer DEFAULT 0,
                  index_rebuilt boolean DEFAULT false,
                  dry_run boolean DEFAULT false,
                  status text,
                  error text
                )
                """
            )
            con.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {SOURCE_RECORDS_TABLE} (
                  ntsb_no text PRIMARY KEY,
                  event_id text,
                  report_url text,
                  newest_report_url text,
                  source_updated_at text,
                  content_hash text NOT NULL,
                  ingested_at timestamptz NOT NULL
                )
                """
            )
            return

        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {INGEST_RUNS_TABLE} (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              started_at TEXT NOT NULL,
              finished_at TEXT,
              source_name TEXT,
              records_seen INTEGER DEFAULT 0,
              records_inserted INTEGER DEFAULT 0,
              records_updated INTEGER DEFAULT 0,
              records_unchanged INTEGER DEFAULT 0,
              index_rebuilt INTEGER DEFAULT 0,
              dry_run INTEGER DEFAULT 0,
              status TEXT,
              error TEXT
            )
            """
        )

    def _ensure_accidents_table(self, con):
        if isinstance(con, PostgresConnection):
            columns_sql = ",\n  ".join(
                f"{column.name} {_postgres_type(column.dtype)}" + (" PRIMARY KEY" if column.name == KEY_COL else "")
                for column in COLUMNS
            )
            con.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} (\n  {columns_sql}\n)")
            con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{TABLE_NAME}_{KEY_COL}_unique ON {TABLE_NAME} ({KEY_COL})")
            return

        columns_sql = ",\n  ".join(
            f"{column.name} {_sqlite_type(column.dtype)}" + (" PRIMARY KEY" if column.name == KEY_COL else "")
            for column in COLUMNS
        )
        con.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} (\n  {columns_sql}\n)")
        con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{TABLE_NAME}_{KEY_COL}_unique ON {TABLE_NAME} ({KEY_COL})")
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {SOURCE_RECORDS_TABLE} (
              ntsb_no TEXT PRIMARY KEY,
              event_id TEXT,
              report_url TEXT,
              newest_report_url TEXT,
              source_updated_at TEXT,
              content_hash TEXT NOT NULL,
              ingested_at TEXT NOT NULL
            )
            """
        )

    def _start_run(self, con, source_name, started_at, dry_run):
        if isinstance(con, PostgresConnection):
            return con.execute(
                f"""
                INSERT INTO {INGEST_RUNS_TABLE} (started_at, source_name, dry_run, status)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (started_at, source_name, dry_run, "running"),
            ).fetchone()["id"]
        cur = con.execute(
            f"""
            INSERT INTO {INGEST_RUNS_TABLE} (started_at, source_name, dry_run, status)
            VALUES (?, ?, ?, ?)
            """,
            (started_at, source_name, int(dry_run), "running"),
        )
        return cur.lastrowid

    def _finish_run(self, con, run_id, status, stats=None, error=None):
        finished_at = datetime.now(timezone.utc).isoformat()
        stats = stats or UpdateStats(0, 0, 0, 0, False, False)
        if isinstance(con, PostgresConnection):
            con.execute(
                f"""
                UPDATE {INGEST_RUNS_TABLE}
                SET finished_at = %s, records_seen = %s, records_inserted = %s,
                    records_updated = %s, records_unchanged = %s, index_rebuilt = %s,
                    dry_run = %s, status = %s, error = %s
                WHERE id = %s
                """,
                (
                    finished_at,
                    stats.records_seen,
                    stats.records_inserted,
                    stats.records_updated,
                    stats.records_unchanged,
                    stats.index_rebuilt,
                    stats.dry_run,
                    status,
                    error,
                    run_id,
                ),
            )
            return

        con.execute(
            f"""
            UPDATE {INGEST_RUNS_TABLE}
            SET finished_at = ?, records_seen = ?, records_inserted = ?,
                records_updated = ?, records_unchanged = ?, index_rebuilt = ?,
                dry_run = ?, status = ?, error = ?
            WHERE id = ?
            """,
            (
                finished_at,
                stats.records_seen,
                stats.records_inserted,
                stats.records_updated,
                stats.records_unchanged,
                int(stats.index_rebuilt),
                int(stats.dry_run),
                status,
                error,
                run_id,
            ),
        )

    def _source_record(self, con, ntsb_no):
        placeholder = _placeholder(con)
        row = con.execute(
            f"SELECT ntsb_no, content_hash FROM {SOURCE_RECORDS_TABLE} WHERE ntsb_no = {placeholder}",
            (ntsb_no,),
        ).fetchone()
        return dict(row) if row else None

    def _upsert_accident(self, con, row, columns):
        values = [_db_value(row.get(column)) for column in columns]
        if isinstance(con, PostgresConnection):
            assignments = ", ".join(f"{column} = EXCLUDED.{column}" for column in columns if column != KEY_COL)
            placeholders = ", ".join(["%s"] * len(columns))
            con.execute(
                f"""
                INSERT INTO {TABLE_NAME} ({", ".join(columns)})
                VALUES ({placeholders})
                ON CONFLICT ({KEY_COL}) DO UPDATE SET {assignments}
                """,
                values,
            )
            return

        assignments = ", ".join(f"{column} = excluded.{column}" for column in columns if column != KEY_COL)
        placeholders = ", ".join(["?"] * len(columns))
        con.execute(
            f"""
            INSERT INTO {TABLE_NAME} ({", ".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT({KEY_COL}) DO UPDATE SET {assignments}
            """,
            values,
        )

    def _upsert_source_record(self, con, **record):
        fields = [
            "ntsb_no",
            "event_id",
            "report_url",
            "newest_report_url",
            "source_updated_at",
            "content_hash",
            "ingested_at",
        ]
        values = [_db_value(record.get(field)) for field in fields]
        if isinstance(con, PostgresConnection):
            placeholders = ", ".join(["%s"] * len(fields))
            assignments = ", ".join(f"{field} = EXCLUDED.{field}" for field in fields if field != "ntsb_no")
            con.execute(
                f"""
                INSERT INTO {SOURCE_RECORDS_TABLE} ({", ".join(fields)})
                VALUES ({placeholders})
                ON CONFLICT (ntsb_no) DO UPDATE SET {assignments}
                """,
                values,
            )
            return

        placeholders = ", ".join(["?"] * len(fields))
        assignments = ", ".join(f"{field} = excluded.{field}" for field in fields if field != "ntsb_no")
        con.execute(
            f"""
            INSERT INTO {SOURCE_RECORDS_TABLE} ({", ".join(fields)})
            VALUES ({placeholders})
            ON CONFLICT(ntsb_no) DO UPDATE SET {assignments}
            """,
            values,
        )

    def _write_doc(self, ntsb_no, text):
        if text is None or pd.isna(text) or not str(text).strip():
            return
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in ntsb_no)
        (self.docs_dir / f"{safe}.txt").write_text(str(text), encoding="utf-8")

    def _invalidate_bm25_cache(self):
        if BM25_CACHE_PATH.exists():
            BM25_CACHE_PATH.unlink()


class PostgresConnection:
    def __init__(self, con):
        self.con = con

    def execute(self, sql, params=()):
        return self.con.execute(sql, params)

    def commit(self):
        self.con.commit()

    def rollback(self):
        self.con.rollback()


def _json_safe(value):
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def _db_value(value):
    value = _json_safe(value)
    if hasattr(value, "item"):
        return value.item()
    return value


def _display_path(path):
    try:
        return Path(path).relative_to(PROJECT_ROOT)
    except ValueError:
        return path


def _placeholder(con):
    return "%s" if isinstance(con, PostgresConnection) else "?"


def _sqlite_type(dtype):
    return {
        "TEXT": "TEXT",
        "INTEGER": "INTEGER",
        "REAL": "REAL",
        "TIMESTAMP": "TEXT",
    }.get(dtype, "TEXT")


def _postgres_type(dtype):
    return {
        "TEXT": "text",
        "INTEGER": "integer",
        "REAL": "double precision",
        "TIMESTAMP": "timestamp",
    }.get(dtype, "text")
