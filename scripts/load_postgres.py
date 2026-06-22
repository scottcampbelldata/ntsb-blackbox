import argparse
import sqlite3
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paths import DB_PATH
from schema_catalog import COLUMNS, TABLE_NAME


INGEST_RUNS_TABLE = "ingest_runs"
SOURCE_RECORDS_TABLE = "source_records"

POSTGRES_TYPE_BY_SQLITE_TYPE = {
    "TEXT": "text",
    "INTEGER": "integer",
    "REAL": "double precision",
    "TIMESTAMP": "timestamp",
}

INDEX_COLUMNS = [
    "event_year",
    "state",
    "broad_phaseof_flight",
    "fatal_injury_count",
    "make",
    "weather_condition",
]


def create_table(con):
    columns_sql = ",\n  ".join(
        f"{column.name} {POSTGRES_TYPE_BY_SQLITE_TYPE.get(column.dtype, 'text')}"
        + (" PRIMARY KEY" if column.name == "ntsb_no" else "")
        for column in COLUMNS
    )
    con.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    con.execute(f"CREATE TABLE {TABLE_NAME} (\n  {columns_sql}\n)")
    for column in INDEX_COLUMNS:
        con.execute(f"CREATE INDEX idx_{TABLE_NAME}_{column} ON {TABLE_NAME} ({column})")


def create_tracking_tables(con):
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


def load_rows(sqlite_path, pg_url, batch_size):
    sqlite_con = sqlite3.connect(sqlite_path)
    sqlite_con.row_factory = sqlite3.Row
    columns = [column.name for column in COLUMNS]
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = (
        f"INSERT INTO {TABLE_NAME} ({', '.join(columns)}) "
        f"VALUES ({placeholders})"
    )

    with psycopg.connect(pg_url) as pg_con:
        with pg_con.transaction():
            create_table(pg_con)
            create_tracking_tables(pg_con)
            cursor = sqlite_con.execute(f"SELECT {', '.join(columns)} FROM {TABLE_NAME}")
            total = 0
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                values = [tuple(row[column] for column in columns) for row in rows]
                with pg_con.cursor() as pg_cur:
                    pg_cur.executemany(insert_sql, values)
                total += len(rows)
            pg_con.execute("ANALYZE accidents")
    sqlite_con.close()
    return total


def main():
    parser = argparse.ArgumentParser(description="Load local NTSB SQLite data into Postgres.")
    parser.add_argument("--database-url", required=True, help="Postgres URL for an owner/migration role.")
    parser.add_argument("--sqlite-path", default=str(DB_PATH), help="Path to local ntsb.db.")
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite_path)
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite database not found: {sqlite_path}")

    total = load_rows(sqlite_path, args.database_url, args.batch_size)
    print(f"Loaded {total} rows into Postgres table {TABLE_NAME}.")


if __name__ == "__main__":
    main()
