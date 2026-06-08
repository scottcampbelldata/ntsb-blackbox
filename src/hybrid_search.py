# src/hybrid_search.py
# ---------------------------------------------------------------------------
# Hybrid retrieval via Reciprocal Rank Fusion (RRF).
#
# Combines the dense (semantic) and BM25 (keyword) rankings into one. The key
# idea, and the reason it works: IGNORE the raw scores entirely. You saw they
# are on incompatible scales (cosine tops out near 0.8, BM25 ran past 30), so
# averaging them would let BM25 bulldoze the cosine signal. RRF combines by
# RANK POSITION instead. Each engine contributes 1/(RRF_K + rank) to every
# accident it ranks. An accident that ranks high in EITHER engine, or decently
# in both, ends up on top. That is how the duck report (semantic found it) and
# the geese report (keyword found it) can both land in one merged list.
#
# This is a module, not a script. compare.py and the app import hybrid_search.
# ---------------------------------------------------------------------------

from search import search as dense_search
from bm25_search import bm25_search

RRF_K = 60  # standard damping constant from the RRF paper; bigger = rank gaps matter less


def _accidents_in_rank_order(results):
    """Collapse a chunk-level result list into an ordered list of unique
    accident ids (each accident kept at its best/first position), plus one
    snippet per accident for display."""
    order, snippet = [], {}
    for _, ntsb_no, text in results:
        if ntsb_no not in snippet:
            snippet[ntsb_no] = text
            order.append(ntsb_no)
    return order, snippet


def hybrid_search(model, vectors, chunk_meta, bm25, query, k=5, pool=50):
    """Pull a pool of candidates from each engine, fuse by RRF, return the top
    k accidents. Returns the same (score, ntsb_no, text) shape as the other two
    retrievers, so any caller can swap one engine for another freely.
    The 'score' here is the RRF score, which is tiny (~0.01-0.03) and only
    meaningful relative to the other hybrid results, not across engines."""
    dense_order, dense_snip = _accidents_in_rank_order(
        dense_search(model, vectors, chunk_meta, query, k=pool))
    kw_order, kw_snip = _accidents_in_rank_order(
        bm25_search(bm25, chunk_meta, query, k=pool))

    fused = {}
    for rank, nid in enumerate(dense_order, start=1):
        fused[nid] = fused.get(nid, 0.0) + 1.0 / (RRF_K + rank)
    for rank, nid in enumerate(kw_order, start=1):
        fused[nid] = fused.get(nid, 0.0) + 1.0 / (RRF_K + rank)

    ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:k]
    return [(score, nid, dense_snip.get(nid) or kw_snip.get(nid)) for nid, score in ranked]
