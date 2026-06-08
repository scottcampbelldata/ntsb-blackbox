# eval/label.py
# ---------------------------------------------------------------------------
# Tool for building the labeled evaluation set BY HAND. This is the part that
# makes the eval credible, and the judgment calls are yours.
#
# Type a query. It pools candidate accidents from BOTH engines (so the label
# pool is as complete as we can make it), shows each one's snippet with a
# number, and you type the numbers that are GENUINELY relevant. It appends the
# labeled query to eval/questions.jsonl, which run_eval.py then scores against.
#
# Why pool from both engines: you can only label what you can see. Pooling both
# makes the relevant set as complete as possible. The honest limitation, for
# the decision log: any truly relevant accident that NEITHER engine surfaced
# cannot be labeled, so recall is measured against this pooled set.
#
# Run from the project root:   python eval/label.py
# ---------------------------------------------------------------------------

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")   # so we can import the engines that live in src/

from sentence_transformers import SentenceTransformer
from search import load_index, search, MODEL_NAME
from bm25_search import build_bm25, bm25_search

QUESTIONS = Path("eval/questions.jsonl")
QUESTIONS.parent.mkdir(parents=True, exist_ok=True)
POOL = 12   # how many candidate accidents from each engine to show for labeling


def dedup_accidents(results):
    order, snip = [], {}
    for _, nid, text in results:
        if nid not in snip:
            snip[nid] = text
            order.append(nid)
    return order, snip


if __name__ == "__main__":
    model = SentenceTransformer(MODEL_NAME)
    vectors, chunk_meta = load_index()
    bm25 = build_bm25(chunk_meta)
    print("\nLabeling tool. Type a query to label. Type quit to exit.\n")

    while True:
        try:
            query = input("label> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            break

        d_order, d_snip = dedup_accidents(search(model, vectors, chunk_meta, query, k=60))
        k_order, k_snip = dedup_accidents(bm25_search(bm25, chunk_meta, query, k=60))

        # pooled candidates: dense's top picks, then any keyword-only ones
        pooled, snippets = [], {}
        for nid in d_order[:POOL] + k_order[:POOL]:
            if nid not in snippets:
                snippets[nid] = d_snip.get(nid) or k_snip.get(nid)
                pooled.append(nid)

        print(f"\nCandidates for: {query}\n")
        for i, nid in enumerate(pooled):
            snip = snippets[nid][:150].replace("\n", " ").strip()
            print(f"  {i:2d}. {nid}  {snip}...")
        print()

        picks = input("Numbers that are RELEVANT (comma-separated), or blank to skip: ").strip()
        if not picks:
            print("skipped\n")
            continue
        try:
            idxs = [int(x) for x in picks.replace(" ", "").split(",") if x != ""]
            relevant = [pooled[i] for i in idxs]
        except (ValueError, IndexError):
            print("could not parse those numbers, skipped\n")
            continue

        notes = input("Optional note on your judgment (or blank): ").strip()
        record = {"query": query, "relevant": relevant, "notes": notes}
        with open(QUESTIONS, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        print(f"saved: {len(relevant)} relevant accidents for this query\n")
