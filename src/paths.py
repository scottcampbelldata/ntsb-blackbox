from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_PATH = DATA_DIR / "raw" / "final_reports_2016-23_cons_2024-12-24.csv"
DB_PATH = DATA_DIR / "ntsb.db"
DOCS_DIR = DATA_DIR / "docs"
INDEX_DIR = DATA_DIR / "index"
VECTORS_PATH = INDEX_DIR / "vectors.npy"
META_PATH = INDEX_DIR / "chunks.jsonl"


def require_file(path, purpose):
    if Path(path).exists():
        return
    rel = Path(path)
    try:
        rel = rel.relative_to(PROJECT_ROOT)
    except ValueError:
        pass
    raise FileNotFoundError(
        f"Missing {purpose}: {rel}\n"
        "Build the local data first:\n"
        "  python src/ingest.py\n"
        "  python src/build_index.py"
    )
