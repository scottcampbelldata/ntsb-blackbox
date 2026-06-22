import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from incremental_ingest import IncrementalUpdater, download_source
from paths import DATA_DIR, RAW_PATH


def main():
    parser = argparse.ArgumentParser(description="Incrementally update Black Box AI from a refreshed NTSB CSV snapshot.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--source-csv", default=None, help="Path to a semicolon-delimited NTSB final-reports CSV.")
    source.add_argument("--source-url", default=None, help="URL for a semicolon-delimited NTSB final-reports CSV.")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"), help="sqlite:///... or postgresql://...")
    parser.add_argument("--source-name", default=None, help="Human-readable source name for ingest audit logs.")
    parser.add_argument("--dry-run", action="store_true", help="Compare records but do not write changes.")
    parser.add_argument("--no-rebuild-index", action="store_true", help="Skip retrieval index rebuild after changes.")
    args = parser.parse_args()

    if args.source_url:
        source_csv = download_source(args.source_url, DATA_DIR / "raw" / "updates")
    else:
        source_csv = Path(args.source_csv) if args.source_csv else RAW_PATH

    updater = IncrementalUpdater(database_url=args.database_url)
    stats = updater.update_from_csv(
        source_csv,
        source_name=args.source_name,
        dry_run=args.dry_run,
        rebuild_index=not args.no_rebuild_index,
    )
    print(json.dumps(stats.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
