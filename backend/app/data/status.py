import sqlite3
from pathlib import Path
from urllib.parse import unquote, urlparse

from backend.app.config import settings


def get_data_status(database_url=None):
    database_url = database_url or settings.database_url
    if database_url.startswith("sqlite:///"):
        return _sqlite_status(database_url)
    if database_url.startswith(("postgresql://", "postgres://")):
        return _postgres_status(database_url)
    return {
        "database": "unknown",
        "ready": False,
        "tracking_ready": False,
        "error": f"Unsupported database URL: {database_url}",
    }


def _sqlite_status(database_url):
    path = _sqlite_path(database_url)
    if not path.exists():
        return {
            "database": "sqlite",
            "ready": False,
            "tracking_ready": False,
            "path": str(path),
            "error": "database file not found",
        }

    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    try:
        status = {
            "database": "sqlite",
            "ready": _table_exists(con, "accidents"),
            "tracking_ready": _table_exists(con, "ingest_runs") and _table_exists(con, "source_records"),
            "path": str(path),
        }
        if status["ready"]:
            status["accident_count"] = _scalar(con, "SELECT COUNT(*) FROM accidents")
        if status["tracking_ready"]:
            status["tracked_source_count"] = _scalar(con, "SELECT COUNT(*) FROM source_records")
            status["latest_ingest"] = _latest_ingest(con)
        return status
    except sqlite3.Error as exc:
        return {
            "database": "sqlite",
            "ready": False,
            "tracking_ready": False,
            "path": str(path),
            "error": str(exc),
        }
    finally:
        con.close()


def _postgres_status(database_url):
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        return {
            "database": "postgres",
            "ready": False,
            "tracking_ready": False,
            "error": str(exc),
        }

    url = "postgresql://" + database_url.removeprefix("postgres://") if database_url.startswith("postgres://") else database_url
    try:
        with psycopg.connect(url, row_factory=dict_row) as con:
            status = {
                "database": "postgres",
                "ready": _pg_table_exists(con, "accidents"),
                "tracking_ready": _pg_table_exists(con, "ingest_runs") and _pg_table_exists(con, "source_records"),
            }
            if status["ready"]:
                status["accident_count"] = con.execute("SELECT COUNT(*) AS count FROM accidents").fetchone()["count"]
            if status["tracking_ready"]:
                status["tracked_source_count"] = con.execute("SELECT COUNT(*) AS count FROM source_records").fetchone()["count"]
                status["latest_ingest"] = con.execute(
                    """
                    SELECT id, started_at, finished_at, source_name, records_seen,
                           records_inserted, records_updated, records_unchanged,
                           index_rebuilt, dry_run, status, error
                    FROM ingest_runs
                    ORDER BY id DESC
                    LIMIT 1
                    """
                ).fetchone()
            return status
    except Exception as exc:
        return {
            "database": "postgres",
            "ready": False,
            "tracking_ready": False,
            "error": str(exc),
        }


def _sqlite_path(database_url):
    parsed = urlparse(database_url)
    return Path(unquote(parsed.path.lstrip("/")))


def _table_exists(con, table_name):
    return (
        con.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        is not None
    )


def _pg_table_exists(con, table_name):
    return (
        con.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
            """,
            (table_name,),
        ).fetchone()
        is not None
    )


def _scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def _latest_ingest(con):
    row = con.execute(
        """
        SELECT id, started_at, finished_at, source_name, records_seen,
               records_inserted, records_updated, records_unchanged,
               index_rebuilt, dry_run, status, error
        FROM ingest_runs
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    return dict(row) if row else None
