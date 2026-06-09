# eval/dump_candidates.py
# ---------------------------------------------------------------------------
# Builds a clean LABELING SHEET for a batch of queries, so labeling can be done
# in one pass (and reviewed) instead of one query at a time at a prompt.
#
# For each query it pools candidate accidents from both engines, then looks up
# each candidate's PROBABLE CAUSE from the SQL table (the NTSB's own one-line
# summary, far better for judging relevance than a random text chunk). This is
# the structured half of the system making the document half easier to label.
#
# Edit the QUERIES list to whatever you want to test, then run from the project
# root:   python eval/dump_candidates.py
# It prints the sheet and also writes it to eval/candidates.txt
# ---------------------------------------------------------------------------

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentence_transformers import SentenceTransformer
from search import load_index, search, MODEL_NAME
from bm25_search import build_bm25, bm25_search
from paths import DB_PATH, require_file

OUT = ROOT / "eval" / "candidates.txt"
PER_ENGINE = 12   # candidates pulled from each engine before pooling

# A deliberately MIXED set: concept queries (wording differs from the reports,
# should favor semantic), exact-term queries (specific terminology, should
# favor keyword), and scenario queries. The mix is what makes the eval fair.
QUERIES = [
    # concept queries
    "pilot lost control in turbulence",
    "ran out of fuel and the engine quit",
    "hard landing that damaged the airplane",
    "lost control maneuvering at low altitude",
    # exact-term queries
    "carburetor icing",
    "fuel contamination",
    "density altitude",
    "wake turbulence encounter",
    "tail rotor failure",
    "magneto failure",
    # scenario queries
    "engine fire after takeoff",
    "landing gear collapse on landing",
    "midair collision",
    "stall spin during base to final turn",
    "controlled flight into terrain",
]


def dedup_ids(results, limit):
    order, seen = [], set()
    for _, nid, _ in results:
        if nid not in seen:
            seen.add(nid)
            order.append(nid)
        if len(order) >= limit:
            break
    return order


def cause_for(con, nid):
    row = con.execute(
        "SELECT probable_cause FROM accidents WHERE ntsb_no = ?", (nid,)
    ).fetchone()
    if row and row[0]:
        return " ".join(str(row[0]).split())[:240]
    return "(no probable cause text)"


if __name__ == "__main__":
    model = SentenceTransformer(MODEL_NAME)
    vectors, chunk_meta = load_index()
    bm25 = build_bm25(chunk_meta)
    require_file(DB_PATH, "SQLite accident database")
    con = sqlite3.connect(DB_PATH)

    lines = []
    for query in QUERIES:
        d = dedup_ids(search(model, vectors, chunk_meta, query, k=60), PER_ENGINE)
        kw = dedup_ids(bm25_search(bm25, chunk_meta, query, k=60), PER_ENGINE)
        pooled = []
        for nid in d + kw:
            if nid not in pooled:
                pooled.append(nid)
        lines.append(f"\n### QUERY: {query}")
        for i, nid in enumerate(pooled):
            lines.append(f"  {i:2d}. {nid}  {cause_for(con, nid)}")
    con.close()

    sheet = "\n".join(lines)
    print(sheet)
    OUT.write_text(sheet, encoding="utf-8")
    print(f"\n\nSaved labeling sheet to {OUT}")
