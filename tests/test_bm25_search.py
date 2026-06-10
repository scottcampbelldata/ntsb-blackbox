import os
import time

import bm25_search as mod
from bm25_search import bm25_search, build_bm25, load_or_build_bm25, tokenize


def meta(texts):
    return [{"ntsb_no": f"A{i}", "chunk_index": 0, "text": t} for i, t in enumerate(texts)]


def test_tokenize_lowercases_and_splits_on_non_alphanumerics():
    assert tokenize("Engine FAILED, at 3,500ft!") == ["engine", "failed", "at", "3", "500ft"]


def test_results_only_include_chunks_sharing_query_terms():
    m = meta([
        "magneto failure during runup",
        "clear skies routine flight",
        "normal landing rollout",
        "uneventful taxi to parking",
    ])
    bm25 = build_bm25(m)
    hits = bm25_search(bm25, m, "magneto", k=4)
    # only one chunk contains the term; argsort must not pad the top k with
    # arbitrary zero-score chunks
    assert [nid for _, nid, _ in hits] == ["A0"]
    assert all(score > 0 for score, _, _ in hits)


def test_query_with_no_overlap_returns_empty():
    m = meta(["alpha bravo", "charlie delta"])
    bm25 = build_bm25(m)
    assert bm25_search(bm25, m, "zulu", k=2) == []


def test_empty_query_returns_empty():
    m = meta(["alpha bravo"])
    bm25 = build_bm25(m)
    assert bm25_search(bm25, m, "!!!", k=2) == []


def test_cache_is_written_and_reused(tmp_path, monkeypatch):
    # three docs so "magneto" (in 1 of 3) carries positive idf; in a 2-doc
    # corpus a term in half the docs has idf 0 and legitimately scores 0
    m = meta(["magneto failure", "routine flight", "normal landing"])
    cache = tmp_path / "bm25.pkl"
    load_or_build_bm25(m, cache_path=cache)
    assert cache.exists()

    def boom(_):
        raise AssertionError("index was rebuilt despite a fresh cache")

    monkeypatch.setattr(mod, "build_bm25", boom)
    bm25 = load_or_build_bm25(m, cache_path=cache)
    assert [nid for _, nid, _ in bm25_search(bm25, m, "magneto", k=1)] == ["A0"]


def test_stale_cache_is_rebuilt(tmp_path, monkeypatch):
    m = meta(["magneto failure", "routine flight", "normal landing"])
    cache = tmp_path / "bm25.pkl"
    source = tmp_path / "chunks.jsonl"
    source.write_text("placeholder", encoding="utf-8")
    load_or_build_bm25(m, cache_path=cache, source_path=source)

    # make the source strictly newer than the cache
    future = time.time() + 60
    os.utime(source, (future, future))

    calls = []
    real_build = build_bm25
    monkeypatch.setattr(mod, "build_bm25", lambda meta: calls.append(1) or real_build(meta))
    load_or_build_bm25(m, cache_path=cache, source_path=source)
    assert calls, "stale cache should trigger a rebuild"
