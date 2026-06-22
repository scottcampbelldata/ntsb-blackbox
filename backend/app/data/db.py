import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from backend.app.config import settings
from sql_guard import validate_sql


@dataclass(frozen=True)
class QueryResult:
    sql: str
    columns: list[str]
    rows: list[dict]
    row_count: int


class QueryExecutionError(RuntimeError):
    pass


def _sqlite_path(database_url):
    if not database_url.startswith("sqlite:///"):
        raise QueryExecutionError(f"Unsupported SQLite URL: {database_url}")
    # Strip exactly the sqlite:/// prefix so an absolute POSIX path keeps its
    # leading slash (sqlite:////abs vs sqlite:///relative), per the SQLAlchemy
    # URL convention. lstrip("/") would corrupt absolute paths on Linux.
    return Path(unquote(database_url[len("sqlite:///"):]))


def _run_sqlite(sql):
    db_path = _sqlite_path(settings.database_url)
    if not db_path.exists():
        raise QueryExecutionError(f"SQLite database not found: {db_path}")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        cursor = con.execute(sql)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description or []]
    finally:
        con.close()
    return [dict(row) for row in rows], columns


def _run_postgres(sql):
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise QueryExecutionError("psycopg is required for Postgres execution.") from exc

    url = settings.database_url
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")

    with psycopg.connect(url, row_factory=dict_row) as con:
        with con.transaction():
            with con.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout = %s", (settings.query_timeout_ms,))
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(sql)
                rows = cur.fetchall()
                columns = [description.name for description in cur.description or []]
                return rows, columns


def run_validated_query(candidate_sql, *, max_rows=None):
    validation = validate_sql(candidate_sql, max_rows=max_rows or settings.max_rows)
    if settings.is_postgres:
        rows, columns = _run_postgres(validation.sql)
    elif settings.is_sqlite:
        rows, columns = _run_sqlite(validation.sql)
    else:
        raise QueryExecutionError(f"Unsupported DATABASE_URL: {settings.database_url}")

    return QueryResult(
        sql=validation.sql,
        columns=columns,
        rows=rows,
        row_count=len(rows),
    )
