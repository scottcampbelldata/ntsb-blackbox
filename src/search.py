# src/search.py
# ---------------------------------------------------------------------------
# Loads the finished semantic index (built once by build_index.py) and lets
# you search it instantly. No embedding of the corpus, no GPU, no two-hour
# wait - that work is already done and saved in data/index/. This only embeds
# your one-line question, which is instant even on a laptop CPU.
#
# Run from the project root:   python src/search.py
#   Type a question, press Enter, see the top matching accident reports.
#   Type quit to exit.
#
# This is also written as a reusable module: the app will import load_index()
# and search() from this exact file later, so it is real project code, not a
# throwaway like the earlier SQL prompt.
# ---------------------------------------------------------------------------

import json

import numpy as np
from sentence_transformers import SentenceTransformer

from paths import META_PATH, VECTORS_PATH, require_file

# These MUST match what build_index.py used. If the model or prefix differs,
# your query vectors would not line up with the stored passage vectors and the
# results would be garbage.
MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def load_index():
    """Read the saved vectors and their metadata back into memory."""
    require_file(VECTORS_PATH, "semantic vector index")
    require_file(META_PATH, "chunk metadata")
    vectors = np.load(VECTORS_PATH)
    chunk_meta = []
    with open(META_PATH, "r", encoding="utf-8") as f:
        for line in f:
            chunk_meta.append(json.loads(line))
    print(f"Loaded {vectors.shape[0]} vectors of dim {vectors.shape[1]}")
    return vectors, chunk_meta


def search(model, vectors, chunk_meta, query, k=5):
    """Embed the question, score it against every stored passage, return top k.
    The vectors were saved normalized, so a plain dot product is the cosine
    similarity, and one matrix multiply scores the whole corpus at once."""
    q = model.encode([QUERY_PREFIX + query], normalize_embeddings=True)[0]
    scores = vectors @ q
    top = np.argsort(scores)[::-1][:k]
    return [(float(scores[i]), chunk_meta[i]["ntsb_no"], chunk_meta[i]["text"]) for i in top]


if __name__ == "__main__":
    model = SentenceTransformer(MODEL_NAME)   # only used to embed your query
    vectors, chunk_meta = load_index()
    print("Index ready. Type a question and press Enter. Type quit to exit.\n")

    while True:
        try:
            query = input("search> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            break
        for score, ntsb_no, text in search(model, vectors, chunk_meta, query, k=5):
            snippet = text[:240].replace("\n", " ").strip()
            print(f"\n[{score:.3f}] {ntsb_no}\n  {snippet}...")
        print()
