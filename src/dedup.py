# src/dedup.py
# ---------------------------------------------------------------------------
# The one shared definition of "collapse chunk-level hits into accidents".
# Every retriever returns (score, ntsb_no, text) tuples at the CHUNK level,
# and several chunks can belong to one accident, so anything that presents
# results per accident needs this dedup. It lives here once; the app, the
# hybrid fuser, and the eval scripts all import it.
# ---------------------------------------------------------------------------


def dedup_accidents(results, k=None):
    """Collapse chunk-level (score, ntsb_no, text) results to one entry per
    accident, keeping each accident's first (best-ranked) hit, in rank order.
    Stops after k accidents when k is given."""
    out, seen = [], set()
    for score, nid, text in results:
        if nid in seen:
            continue
        seen.add(nid)
        out.append((score, nid, text))
        if k is not None and len(out) >= k:
            break
    return out
