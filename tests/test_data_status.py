import sqlite3

from backend.app.data.status import get_data_status


def test_data_status_reports_missing_sqlite_database(tmp_path):
    status = get_data_status(f"sqlite:///{tmp_path / 'missing.db'}")

    assert status["database"] == "sqlite"
    assert status["ready"] is False
    assert status["tracking_ready"] is False
    assert status["error"] == "database file not found"


def test_data_status_reports_latest_ingest_run(tmp_path):
    db_path = tmp_path / "ntsb.db"
    con = sqlite3.connect(db_path)
    try:
        con.execute("CREATE TABLE accidents (ntsb_no TEXT PRIMARY KEY)")
        con.execute("CREATE TABLE source_records (ntsb_no TEXT PRIMARY KEY, content_hash TEXT)")
        con.execute(
            """
            CREATE TABLE ingest_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              started_at TEXT,
              finished_at TEXT,
              source_name TEXT,
              records_seen INTEGER,
              records_inserted INTEGER,
              records_updated INTEGER,
              records_unchanged INTEGER,
              index_rebuilt INTEGER,
              dry_run INTEGER,
              status TEXT,
              error TEXT
            )
            """
        )
        con.execute("INSERT INTO accidents (ntsb_no) VALUES ('A'), ('B')")
        con.execute("INSERT INTO source_records (ntsb_no, content_hash) VALUES ('A', 'one')")
        con.execute(
            """
            INSERT INTO ingest_runs (
              started_at, finished_at, source_name, records_seen, records_inserted,
              records_updated, records_unchanged, index_rebuilt, dry_run, status, error
            )
            VALUES ('2026-06-21T00:00:00Z', '2026-06-21T00:01:00Z', 'unit-test.csv',
                    2, 1, 0, 1, 0, 0, 'ok', NULL)
            """
        )
        con.commit()
    finally:
        con.close()

    status = get_data_status(f"sqlite:///{db_path}")

    assert status["ready"] is True
    assert status["tracking_ready"] is True
    assert status["accident_count"] == 2
    assert status["tracked_source_count"] == 1
    assert status["latest_ingest"]["source_name"] == "unit-test.csv"
    assert status["latest_ingest"]["status"] == "ok"
