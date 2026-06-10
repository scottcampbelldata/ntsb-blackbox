# src/hybrid_search.py
# ---------------------------------------------------------------------------
# Hybrid retrieval via Reciprocal Rank Fusion (RRF).
#
# Combines the dense (semantic) and BM25 (keyword) rankings into one. The key
# idea, and the reason it works: IGNORE the raw scores entirely. They are on
# incompatible scales (cosine tops out near 0.8, BM25 can run past 30), so
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
from dedup import dedup_accidents

RRF_K = 60  # standard damping constant from the RRF paper; bigger = rank gaps matter less


def rrf_fuse(rankings, k=None, rrf_k=RRF_K):
    """Fuse ranked id lists by Reciprocal Rank Fusion: each list contributes
    1/(rrf_k + rank) for every id it ranks. Returns (id, score) pairs sorted
    best first, capped at k when k is given."""
    fused = {}
    for order in rankings:
        for rank, nid in enumerate(order, start=1):
            fused[nid] = fused.get(nid, 0.0) + 1.0 / (rrf_k + rank)
    ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)
    return ranked if k is None else ranked[:k]


def hybrid_search(model, vectors, chunk_meta, bm25, query, k=5, pool=50):
    """Pull a pool of candidates from each engine, fuse by RRF, return the top
    k accidents. Returns the same (score, ntsb_no, text) shape as the other two
    retrievers, so any caller can swap one engine for another freely.
    The 'score' here is the RRF score, which is tiny (~0.01-0.03) and only
    meaningful relative to the other hybrid results, not across engines."""
    dense = dedup_accidents(dense_search(model, vectors, chunk_meta, query, k=pool))
    keyword = dedup_accidents(bm25_search(bm25, chunk_meta, query, k=pool))

    # one display snippet per accident; the dense snippet wins when both have one
    snippets = {}
    for _, nid, text in keyword + dense:
        snippets[nid] = text

    ranked = rrf_fuse(
        [[nid for _, nid, _ in dense], [nid for _, nid, _ in keyword]], k=k
    )
    return [(score, nid, snippets[nid]) for nid, score in ranked]
