import sqlite3

from incremental_ingest import IncrementalUpdater, SOURCE_RECORDS_TABLE, stable_record_hash


def _write_csv(path, rows):
    columns = [
        "ntsb_no",
        "event_date",
        "state",
        "fatal_injury_count",
        "report_url",
        "rep_text",
    ]
    lines = [";".join(columns)]
    for row in rows:
        lines.append(";".join(str(row.get(column, "")) for column in columns))
    path.write_text("\n".join(lines), encoding="utf-8")


def test_stable_record_hash_changes_when_content_changes():
    a = stable_record_hash({"ntsb_no": "A", "rep_text": "one"}, ["ntsb_no", "rep_text"])
    b = stable_record_hash({"ntsb_no": "A", "rep_text": "two"}, ["ntsb_no", "rep_text"])
    assert a != b


def test_incremental_update_inserts_then_skips_unchanged_records(tmp_path):
    db_path = tmp_path / "ntsb.db"
    docs_dir = tmp_path / "docs"
    csv_path = tmp_path / "source.csv"
    _write_csv(
        csv_path,
        [
            {
                "ntsb_no": "TEST001",
                "event_date": "2024-01-02",
                "state": "Ohio",
                "fatal_injury_count": "1",
                "report_url": "https://example.test/report.pdf",
                "rep_text": "Initial narrative text.",
            }
        ],
    )

    updater = IncrementalUpdater(database_url=f"sqlite:///{db_path}", docs_dir=docs_dir)
    first = updater.update_from_csv(csv_path, dry_run=False, rebuild_index=False)
    second = updater.update_from_csv(csv_path, dry_run=False, rebuild_index=False)

    assert first.records_inserted == 1
    assert first.records_updated == 0
    assert first.records_unchanged == 0
    assert second.records_inserted == 0
    assert second.records_updated == 0
    assert second.records_unchanged == 1
    assert (docs_dir / "TEST001.txt").read_text(encoding="utf-8") == "Initial narrative text."

    con = sqlite3.connect(db_path)
    try:
        state = con.execute("SELECT state FROM accidents WHERE ntsb_no = 'TEST001'").fetchone()[0]
        source_count = con.execute(f"SELECT COUNT(*) FROM {SOURCE_RECORDS_TABLE}").fetchone()[0]
    finally:
        con.close()
    assert state == "Ohio"
    assert source_count == 1


def test_incremental_update_updates_changed_records(tmp_path):
    db_path = tmp_path / "ntsb.db"
    docs_dir = tmp_path / "docs"
    csv_path = tmp_path / "source.csv"
    updater = IncrementalUpdater(database_url=f"sqlite:///{db_path}", docs_dir=docs_dir)

    _write_csv(csv_path, [{"ntsb_no": "TEST001", "event_date": "2024-01-02", "state": "Ohio", "rep_text": "Old text."}])
    updater.update_from_csv(csv_path, dry_run=False, rebuild_index=False)
    _write_csv(csv_path, [{"ntsb_no": "TEST001", "event_date": "2024-01-02", "state": "Texas", "rep_text": "New text."}])
    stats = updater.update_from_csv(csv_path, dry_run=False, rebuild_index=False)

    assert stats.records_inserted == 0
    assert stats.records_updated == 1
    assert (docs_dir / "TEST001.txt").read_text(encoding="utf-8") == "New text."

    con = sqlite3.connect(db_path)
    try:
        state = con.execute("SELECT state FROM accidents WHERE ntsb_no = 'TEST001'").fetchone()[0]
    finally:
        con.close()
    assert state == "Texas"


def test_dry_run_counts_changes_without_writing_accidents_or_docs(tmp_path):
    db_path = tmp_path / "ntsb.db"
    docs_dir = tmp_path / "docs"
    csv_path = tmp_path / "source.csv"
    _write_csv(csv_path, [{"ntsb_no": "TEST001", "event_date": "2024-01-02", "state": "Ohio", "rep_text": "Text."}])

    updater = IncrementalUpdater(database_url=f"sqlite:///{db_path}", docs_dir=docs_dir)
    stats = updater.update_from_csv(csv_path, dry_run=True, rebuild_index=False)

    assert stats.records_inserted == 1
    assert stats.dry_run is True
    assert not (docs_dir / "TEST001.txt").exists()

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute("SELECT COUNT(*) FROM accidents").fetchone()[0]
    finally:
        con.close()
    assert rows == 0
