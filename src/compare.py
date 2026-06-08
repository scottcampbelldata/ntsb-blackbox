# src/compare.py
# ---------------------------------------------------------------------------
# Runs ONE query through all THREE retrievers and shows them side by side:
#   - SEMANTIC (dense vectors): matches meaning
#   - KEYWORD  (BM25):          matches exact words
#   - HYBRID   (RRF fusion):    combines the two by rank
#
# The thing to watch is the HYBRID list and the "WHAT HYBRID KEPT" block at the
# bottom: hybrid should contain the strong hits from BOTH of the other engines,
# which is the entire reason for fusing them.
#
# Run from the project root:   python src/compare.py
#
# Reminder: the score in each block is on a different scale (cosine ~0-0.8,
# BM25 unbounded, RRF ~0.01-0.03). Compare rankings and accident ids across
# blocks, never the raw numbers.
# ---------------------------------------------------------------------------

from sentence_transformers import SentenceTransformer

from search import load_index, search, MODEL_NAME
from bm25_search import build_bm25, bm25_search
from hybrid_search import hybrid_search

K = 5


def show(title, results):
    print(f"\n--- {title} ---")
    for score, ntsb_no, text in results:
        snippet = text[:150].replace("\n", " ").strip()
        print(f"[{score:.3f}] {ntsb_no}  {snippet}...")


if __name__ == "__main__":
    model = SentenceTransformer(MODEL_NAME)
    vectors, chunk_meta = load_index()
    bm25 = build_bm25(chunk_meta)
    print("\nAll three engines ready. Type a question. Type quit to exit.\n")

    while True:
        try:
            query = input("compare> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            break

        dense_results = search(model, vectors, chunk_meta, query, k=K)
        keyword_results = bm25_search(bm25, chunk_meta, query, k=K)
        hybrid_results = hybrid_search(model, vectors, chunk_meta, bm25, query, k=K)

        show("SEMANTIC (meaning)", dense_results)
        show("KEYWORD (BM25, exact words)", keyword_results)
        show("HYBRID (RRF fusion)", hybrid_results)

        # The payoff: show that hybrid's picks came from BOTH engines.
        dense_ids = {r[1] for r in dense_results}
        keyword_ids = {r[1] for r in keyword_results}
        hybrid_ids = {r[1] for r in hybrid_results}
        print("\n--- WHAT HYBRID KEPT ---")
        print(f"hybrid picks also in SEMANTIC top {K}: {sorted(hybrid_ids & dense_ids) or 'none'}")
        print(f"hybrid picks also in KEYWORD top {K}:  {sorted(hybrid_ids & keyword_ids) or 'none'}")
        print()
