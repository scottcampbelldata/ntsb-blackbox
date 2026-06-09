# eval/run_eval.py
# ---------------------------------------------------------------------------
# Scores semantic / keyword / hybrid against the labeled set, and now prints a
# PER-QUERY breakdown so you can see WHERE the engines differ. The aggregate
# averages hide that; the per-query table is where the real finding lives.
#
# Metrics (accident level, deduped from chunks):
#   Recall@K : of the labeled-relevant accidents, what fraction made top K
#   MRR      : 1 / rank of the first relevant accident
#   Hit@K    : did at least one relevant accident make the top K
#
# Run from the project root:   python eval/run_eval.py
# ---------------------------------------------------------------------------

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentence_transformers import SentenceTransformer
from search import load_index, search, MODEL_NAME
from bm25_search import build_bm25, bm25_search
from hybrid_search import hybrid_search

QUESTIONS = ROOT / "eval" / "questions.jsonl"
K = 5
POOL = 60


def dedup(results):
    order, seen = [], set()
    for _, nid, _ in results:
        if nid not in seen:
            seen.add(nid)
            order.append(nid)
    return order


def metrics(ranked, relevant, k=K):
    relevant = set(relevant)
    topk = ranked[:k]
    hits = sum(1 for nid in topk if nid in relevant)
    recall = hits / len(relevant) if relevant else 0.0
    hit = 1.0 if hits > 0 else 0.0
    rr = 0.0
    for rank, nid in enumerate(ranked, start=1):
        if nid in relevant:
            rr = 1.0 / rank
            break
    return recall, rr, hit


if __name__ == "__main__":
    if not QUESTIONS.exists():
        print("No labeled set found. Run  python eval/label.py  first.")
        sys.exit()

    queries = [json.loads(l) for l in open(QUESTIONS, encoding="utf-8") if l.strip()]
    queries = [q for q in queries if q.get("relevant")]
    if not queries:
        print("No labeled queries with relevant accident ids found.")
        sys.exit()
    print(f"Loaded {len(queries)} labeled queries.\n")

    model = SentenceTransformer(MODEL_NAME)
    vectors, chunk_meta = load_index()
    bm25 = build_bm25(chunk_meta)

    agg = {"semantic": [], "keyword": [], "hybrid": []}
    per_query = []
    wins = {"semantic": 0, "keyword": 0, "hybrid": 0, "tie": 0}

    for q in queries:
        query, relevant = q["query"], q["relevant"]
        d = dedup(search(model, vectors, chunk_meta, query, k=POOL))
        kw = dedup(bm25_search(bm25, chunk_meta, query, k=POOL))
        hy = [nid for _, nid, _ in hybrid_search(model, vectors, chunk_meta, bm25, query, k=POOL)]

        sm, km, hm = metrics(d, relevant), metrics(kw, relevant), metrics(hy, relevant)
        agg["semantic"].append(sm)
        agg["keyword"].append(km)
        agg["hybrid"].append(hm)

        # who had the best Recall@5 on this query (ties noted)
        recalls = {"semantic": sm[0], "keyword": km[0], "hybrid": hm[0]}
        best = max(recalls.values())
        leaders = [name for name, r in recalls.items() if abs(r - best) < 1e-9]
        wins["tie" if len(leaders) > 1 else leaders[0]] += 1

        per_query.append((query, len(relevant), sm[0], km[0], hm[0]))

    # ---- per-query Recall@5 ----
    print(f"{'query (n = relevant)':<42}{'sem':>6}{'key':>6}{'hyb':>6}")
    print("-" * 60)
    for query, n, s, k, h in per_query:
        label = f"{query[:30]} (n={n})"
        print(f"{label:<42}{s:>6.2f}{k:>6.2f}{h:>6.2f}")

    # ---- aggregate ----
    print(f"\n{'engine':<10}{'Recall@'+str(K):>12}{'MRR':>8}{'Hit@'+str(K):>8}")
    print("-" * 38)
    for name, rows in agg.items():
        n = len(rows)
        print(f"{name:<10}{sum(r[0] for r in rows)/n:>12.3f}"
              f"{sum(r[1] for r in rows)/n:>8.3f}{sum(r[2] for r in rows)/n:>8.3f}")

    # ---- who won each query on Recall@5 ----
    print(f"\nRecall@5 wins per engine (out of {len(queries)} queries):")
    for name in ("semantic", "keyword", "hybrid", "tie"):
        print(f"  {name:<10} {wins[name]}")
