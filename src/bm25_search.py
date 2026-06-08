# src/bm25_search.py
# ---------------------------------------------------------------------------
# Keyword search over the SAME chunks the semantic index uses, via BM25.
#
# BM25 is the classic keyword-ranking algorithm (it is roughly what a search
# engine did before vectors). It matches the literal WORDS in your query
# against the literal words in each passage, and scores a passage higher when
# it contains your rare query words many times. It has no idea what words
# MEAN - "bird" and "avian" are unrelated strangers to it. That literalness is
# its weakness on paraphrase and its strength on exact-term queries.
#
# Run from the project root:   python src/bm25_search.py
# ---------------------------------------------------------------------------

import json
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

META_PATH = Path("data/index/chunks.jsonl")


def tokenize(text):
    """Lowercase and split into word tokens. BM25 compares these tokens
    literally, so 'Landing' and 'landing' must be lowercased to match, and
    'bird' will NOT match 'birds' (no stemming) - a real limitation worth
    knowing about."""
    return re.findall(r"[a-z0-9]+", text.lower())


def load_chunks():
    chunk_meta = []
    with open(META_PATH, "r", encoding="utf-8") as f:
        for line in f:
            chunk_meta.append(json.loads(line))
    return chunk_meta


def build_bm25(chunk_meta):
    """Tokenize every chunk and build the BM25 index in memory. Takes a few
    seconds over 74k chunks and needs no GPU. Position i in this index is the
    SAME chunk as row i of the dense vectors, so the two are directly
    comparable by index."""
    print(f"Building BM25 index over {len(chunk_meta)} chunks...")
    tokenized_corpus = [tokenize(m["text"]) for m in chunk_meta]
    return BM25Okapi(tokenized_corpus)


def bm25_search(bm25, chunk_meta, query, k=5):
    scores = bm25.get_scores(tokenize(query))
    top = np.argsort(scores)[::-1][:k]
    return [(float(scores[i]), chunk_meta[i]["ntsb_no"], chunk_meta[i]["text"]) for i in top]


if __name__ == "__main__":
    chunk_meta = load_chunks()
    bm25 = build_bm25(chunk_meta)
    print("BM25 ready. Type a question and press Enter. Type quit to exit.\n")

    while True:
        try:
            query = input("keyword> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            break
        for score, ntsb_no, text in bm25_search(bm25, chunk_meta, query, k=5):
            snippet = text[:240].replace("\n", " ").strip()
            print(f"\n[{score:.2f}] {ntsb_no}\n  {snippet}...")
        print()
