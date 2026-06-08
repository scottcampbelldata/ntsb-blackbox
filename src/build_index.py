# src/build_index.py
# ---------------------------------------------------------------------------
# Builds the semantic search index over the accident narratives.
# This is the RETRIEVAL half of the system (the "R" in RAG): it lets you find
# the most relevant report passages for a plain-English question, by meaning
# rather than by exact keyword.
#
# Run ONCE from the project root:   python src/build_index.py
#   It reads data/docs/*.txt, splits them into passages, turns each passage
#   into a vector with an embedding model, saves the index to data/index/,
#   then runs a few demo searches so you can see it work.
#
# One-time install first:           pip install sentence-transformers
# ---------------------------------------------------------------------------

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

DOCS = Path("data/docs")
INDEX_DIR = Path("data/index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

VECTORS_PATH = INDEX_DIR / "vectors.npy"     # the embeddings, one row per chunk
META_PATH = INDEX_DIR / "chunks.jsonl"       # what each row of vectors refers to

# The embedding model. Small, fast, good quality. Swappable later in one line
# if we want something stronger. bge models want a short instruction prefix on
# the QUERY (not on the stored passages) for retrieval, handled below.
MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# A full report is too long to embed as one vector, so we cut each narrative
# into overlapping windows of words. Overlap keeps a sentence from being split
# across a boundary and lost.
CHUNK_WORDS = 200
CHUNK_OVERLAP = 40


def chunk_text(text, size=CHUNK_WORDS, overlap=CHUNK_OVERLAP):
    """Split one narrative into overlapping word-windows."""
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = start + size
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap   # step back by the overlap before the next window
    return chunks


def build():
    model = SentenceTransformer(MODEL_NAME)

    chunk_texts = []
    chunk_meta = []
    files = sorted(DOCS.glob("*.txt"))
    print(f"Reading {len(files)} narratives...")
    for fp in files:
        ntsb_no = fp.stem                       # the filename is the accident id
        text = fp.read_text(encoding="utf-8")
        for i, ch in enumerate(chunk_text(text)):
            chunk_texts.append(ch)
            # metadata ties each vector back to the accident it came from, so a
            # search result can cite a real NtsbNo. This id is the join key back
            # to the SQL table too, which is what lets the two halves talk later.
            chunk_meta.append({"ntsb_no": ntsb_no, "chunk_index": i, "text": ch})

    print(f"Created {len(chunk_texts)} chunks. Embedding now (this is the slow part)...")
    vectors = model.encode(
        chunk_texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,   # makes a plain dot product equal cosine similarity
    )
    vectors = np.asarray(vectors, dtype=np.float32)

    np.save(VECTORS_PATH, vectors)
    with open(META_PATH, "w", encoding="utf-8") as f:
        for m in chunk_meta:
            f.write(json.dumps(m) + "\n")

    print(f"\nSaved {vectors.shape[0]} vectors of dim {vectors.shape[1]} to {VECTORS_PATH}")
    print(f"Saved chunk metadata to {META_PATH}")
    return model, vectors, chunk_meta


def search(model, vectors, chunk_meta, query, k=5):
    """Embed the question, score it against every chunk, return the top k.
    Because everything is normalized, similarity is just one matrix multiply."""
    q = model.encode([QUERY_PREFIX + query], normalize_embeddings=True)[0]
    scores = vectors @ q                       # cosine similarity for all chunks at once
    top = np.argsort(scores)[::-1][:k]         # highest scores first
    results = []
    for idx in top:
        m = chunk_meta[idx]
        results.append((float(scores[idx]), m["ntsb_no"], m["text"]))
    return results


if __name__ == "__main__":
    model, vectors, chunk_meta = build()

    # Three demo searches so you can eyeball whether retrieval actually works.
    demos = [
        "pilot error recovering from a bounced landing",
        "engine failure due to fuel exhaustion",
        "loss of control flying into instrument weather conditions",
    ]
    for q in demos:
        print("\n" + "=" * 70)
        print(f"QUERY: {q}")
        print("=" * 70)
        for score, ntsb_no, text in search(model, vectors, chunk_meta, q, k=3):
            snippet = text[:240].replace("\n", " ")
            print(f"\n[{score:.3f}] {ntsb_no}")
            print(f"  {snippet}...")
