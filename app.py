# app.py  -  Black Box: NTSB aviation safety explorer
# ---------------------------------------------------------------------------
# Two halves on one screen:
#   1. Search the narratives  -> retrieval (semantic / keyword / hybrid), with
#      the router's classification, results led by each accident's probable
#      cause from the SQL table plus the matched passage as relevance evidence.
#   2. Data analyses          -> prebuilt SQL queries, each shown with its SQL,
#      a result table, and a readable horizontal bar chart.
#
# NO LLM, by design: free text only ever drives RETRIEVAL and the structured
# side runs only hand-written queries. Safe to host on a public link.
#
# Run locally:   python app.py     (opens http://localhost:7860)
# ---------------------------------------------------------------------------

import sqlite3
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import gradio as gr
from sentence_transformers import SentenceTransformer

from search import load_index, search as dense_search, MODEL_NAME
from bm25_search import load_or_build_bm25, bm25_search
from hybrid_search import hybrid_search
from dedup import dedup_accidents
from paths import BM25_CACHE_PATH, DB_PATH, META_PATH, require_file
from router import route
from sql_tool import accident_count, analysis_key, list_analyses, run_analysis
from ui_helpers import context_line, make_chart, router_badge

# Chunk-level hits pulled before collapsing to accidents. Deep enough that a
# topic-saturated query (one accident contributing many chunks) still yields
# five distinct accidents.
POOL = 80

try:
    print("Loading model and indexes (one-time startup)...")
    require_file(DB_PATH, "SQLite accident database")
    MODEL = SentenceTransformer(MODEL_NAME)
    VECTORS, CHUNK_META = load_index()
    BM25 = load_or_build_bm25(CHUNK_META, BM25_CACHE_PATH, source_path=META_PATH)
    N_ACCIDENTS = accident_count()
    print("Ready.")
except FileNotFoundError as exc:
    raise RuntimeError(
        "Black Box could not find its local data files.\n\n"
        f"{exc}\n\n"
        "The code repo intentionally does not commit data/. For local use, download "
        "the source CSV into data/raw/, then run the two build commands above."
    ) from exc


def _accident_meta(ntsb_nos):
    if not ntsb_nos:
        return {}
    placeholders = ",".join("?" * len(ntsb_nos))
    cols = ("ntsb_no, event_year, city, state, make, model, "
            "fatal_injury_count, serious_injury_count, probable_cause, report_url")
    with closing(sqlite3.connect(DB_PATH)) as con:
        rows = con.execute(
            f"SELECT {cols} FROM accidents WHERE ntsb_no IN ({placeholders})", ntsb_nos
        ).fetchall()
    out = {}
    for r in rows:
        out[r[0]] = {
            "event_year": r[1], "city": r[2], "state": r[3],
            "make": r[4], "model": r[5],
            "fatal_injury_count": r[6], "serious_injury_count": r[7],
            "probable_cause": r[8], "report_url": r[9],
        }
    return out


def do_search(query, retriever):
    if not query or not query.strip():
        return "Enter a question above, or click an example.", ""

    decision, sql_hits, ret_hits = route(query)
    badge = router_badge(decision, sql_hits, ret_hits)

    if retriever == "Keyword (BM25)":
        raw = bm25_search(BM25, CHUNK_META, query, k=POOL)
    elif retriever == "Hybrid (RRF)":
        raw = hybrid_search(MODEL, VECTORS, CHUNK_META, BM25, query, k=5, pool=POOL)
    else:
        raw = dense_search(MODEL, VECTORS, CHUNK_META, query, k=POOL)

    hits = dedup_accidents(raw, k=5)
    if not hits:
        return badge, "No matching passages found. Try a more specific aviation term or switch retrievers."

    meta = _accident_meta([nid for _, nid, _ in hits])

    cards = []
    for i, (score, nid, text) in enumerate(hits, start=1):
        m = meta.get(nid, {})
        url = m.get("report_url")
        cite = f"[{nid}]({url})" if url else f"`{nid}`"
        context = context_line(m)
        cause = m.get("probable_cause")
        cause = " ".join(str(cause).split())[:500] if cause else "(probable cause not available)"
        snippet = " ".join(str(text).split())[:240]
        card = (
            f"**{i}. {cite}**" + (f"  ·  {context}" if context else "") + "\n\n"
            f"**Probable cause:** {cause}\n\n"
            f"**Matched passage** ({retriever}, score {score:.3f}): …{snippet}…"
        )
        cards.append(card)

    return badge, "\n\n---\n\n".join(cards)


def do_analysis(label):
    key = analysis_key(label)
    if key is None:
        raise gr.Error(f"Unknown analysis: {label}")
    sql, df = run_analysis(key)
    return sql, df, make_chart(df, label)


ANALYSIS_LABELS = [lab for _, lab in list_analyses()]

EXAMPLES = [
    "why do pilots lose control in icing conditions",
    "engine failure shortly after takeoff",
    "spatial disorientation at night over water",
    "carburetor icing during descent",
    "bird strike on takeoff",
]

with gr.Blocks(title="Black Box - NTSB Aviation Safety Explorer") as demo:
    gr.Markdown(
        "# Black Box\n"
        f"### Question answering over {N_ACCIDENTS:,} NTSB aviation accident reports\n"
        "A hybrid system over a **structured table** (counts, statistics) and the "
        "**accident narratives**. Three retrieval strategies (semantic, keyword, and "
        "hybrid) were evaluated against a hand-labeled query set; switch between them "
        "below and compare. Every statistic is a real SQL query shown with its result, "
        "and every report is cited to its official NTSB record. No text generation: the "
        "engines are shown directly, so there is nothing for a model to invent."
    )

    with gr.Tab("Search the reports"):
        gr.Markdown("Ask about what happened in accidents. Search runs over the report narratives.")
        with gr.Row():
            q = gr.Textbox(label="Your question", placeholder="why do pilots lose control in icing conditions", scale=4)
            retriever = gr.Radio(
                ["Semantic", "Keyword (BM25)", "Hybrid (RRF)"],
                value="Semantic", label="Retriever", scale=1,
            )
        search_btn = gr.Button("Search", variant="primary")
        gr.Examples(examples=EXAMPLES, inputs=q)
        router_out = gr.Markdown()
        results_out = gr.Markdown()
        search_btn.click(do_search, [q, retriever], [router_out, results_out])
        q.submit(do_search, [q, retriever], [router_out, results_out])

    with gr.Tab("Data analyses"):
        gr.Markdown("Prebuilt statistics. Each is a hand-written SQL query; the exact SQL is shown so the number is always traceable.")
        analysis_pick = gr.Dropdown(ANALYSIS_LABELS, value=ANALYSIS_LABELS[0], label="Analysis")
        run_btn = gr.Button("Run", variant="primary")
        sql_out = gr.Code(label="SQL that ran", language="sql")
        with gr.Row():
            table_out = gr.Dataframe(label="Result")
            chart_out = gr.Plot(label="Chart")
        run_btn.click(do_analysis, [analysis_pick], [sql_out, table_out, chart_out])

    gr.Markdown(
        "---\nData: US NTSB aviation accident final reports, 2016-2023 (public domain). "
        "Years 2020-2021 are absent from this dataset, and recent years are still filling "
        "in due to investigation lag. Built as a portfolio project."
    )

if __name__ == "__main__":
    demo.launch()
