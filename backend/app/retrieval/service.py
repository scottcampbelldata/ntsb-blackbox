import sqlite3
from contextlib import closing

from backend.app.config import settings
from bm25_search import bm25_search, load_chunks, load_or_build_bm25
from dedup import dedup_accidents
from paths import BM25_CACHE_PATH, DB_PATH, META_PATH


class RetrievalService:
    def __init__(self):
        self._chunk_meta = None
        self._bm25 = None

    def _load(self):
        if self._chunk_meta is None:
            self._chunk_meta = load_chunks()
        if self._bm25 is None:
            self._bm25 = load_or_build_bm25(self._chunk_meta, BM25_CACHE_PATH, source_path=META_PATH)

    def search(self, question, *, k=None):
        self._load()
        raw = bm25_search(self._bm25, self._chunk_meta, question, k=settings.retrieval_pool)
        hits = dedup_accidents(raw, k=k or settings.retrieval_k)
        meta = _accident_meta([ntsb_no for _, ntsb_no, _ in hits])
        results = []
        for score, ntsb_no, text in hits:
            m = meta.get(ntsb_no, {})
            results.append(
                {
                    "ntsb_no": ntsb_no,
                    "score": score,
                    "matched_passage": " ".join(str(text).split())[:700],
                    "probable_cause": " ".join(str(m.get("probable_cause") or "").split())[:700],
                    "report_url": m.get("report_url"),
                    "event_year": m.get("event_year"),
                    "city": m.get("city"),
                    "state": m.get("state"),
                    "make": m.get("make"),
                    "model": m.get("model"),
                }
            )
        return results


def _accident_meta(ntsb_nos):
    if not ntsb_nos or not DB_PATH.exists():
        return {}
    placeholders = ",".join("?" * len(ntsb_nos))
    cols = (
        "ntsb_no, event_year, city, state, make, model, "
        "probable_cause, report_url"
    )
    with closing(sqlite3.connect(DB_PATH)) as con:
        rows = con.execute(
            f"SELECT {cols} FROM accidents WHERE ntsb_no IN ({placeholders})", ntsb_nos
        ).fetchall()
    return {
        row[0]: {
            "event_year": row[1],
            "city": row[2],
            "state": row[3],
            "make": row[4],
            "model": row[5],
            "probable_cause": row[6],
            "report_url": row[7],
        }
        for row in rows
    }


retrieval_service = RetrievalService()
