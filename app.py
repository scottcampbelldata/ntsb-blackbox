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
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import gradio as gr
from sentence_transformers import SentenceTransformer

from search import load_index, search as dense_search, MODEL_NAME
from bm25_search import build_bm25, bm25_search
from hybrid_search import hybrid_search
from paths import DB_PATH, require_file
from router import route
from sql_tool import list_analyses, run_analysis

ORANGE = "#e8772e"

try:
    print("Loading model and indexes (one-time startup)...")
    require_file(DB_PATH, "SQLite accident database")
    MODEL = SentenceTransformer(MODEL_NAME)
    VECTORS, CHUNK_META = load_index()
    BM25 = build_bm25(CHUNK_META)
    print("Ready.")
except FileNotFoundError as exc:
    raise RuntimeError(
        "Black Box could not find its local data files.\n\n"
        f"{exc}\n\n"
        "The code repo intentionally does not commit data/. For local use, download "
        "the source CSV into data/raw/, then run the two build commands above."
    ) from exc


def _dedup_to_accidents(results, k=5):
    out, seen = [], set()
    for score, nid, text in results:
        if nid not in seen:
            seen.add(nid)
            out.append((score, nid, text))
        if len(out) >= k:
            break
    return out


def _accident_meta(ntsb_nos):
    if not ntsb_nos:
        return {}
    con = sqlite3.connect(DB_PATH)
    placeholders = ",".join("?" * len(ntsb_nos))
    cols = ("ntsb_no, event_year, city, state, make, model, "
            "fatal_injury_count, serious_injury_count, probable_cause, report_url")
    rows = con.execute(
        f"SELECT {cols} FROM accidents WHERE ntsb_no IN ({placeholders})", ntsb_nos
    ).fetchall()
    con.close()
    out = {}
    for r in rows:
        out[r[0]] = {
            "event_year": r[1], "city": r[2], "state": r[3],
            "make": r[4], "model": r[5],
            "fatal_injury_count": r[6], "serious_injury_count": r[7],
            "probable_cause": r[8], "report_url": r[9],
        }
    return out


def _context_line(m):
    bits = []
    mk = m.get("make")
    if mk:
        md = m.get("model")
        bits.append(f"{str(mk).title()}{(' ' + str(md)) if md else ''}")
    if m.get("event_year"):
        bits.append(str(int(m["event_year"])))
    loc = ", ".join(p for p in [m.get("city"), m.get("state")] if p)
    if loc:
        bits.append(loc)
    fatal = m.get("fatal_injury_count") or 0
    serious = m.get("serious_injury_count") or 0
    if fatal and fatal > 0:
        bits.append(f"{int(fatal)} fatal")
    elif serious and serious > 0:
        bits.append(f"{int(serious)} serious")
    return "  \u00b7  ".join(bits)


def do_search(query, retriever):
    if not query or not query.strip():
        return "Enter a question above, or click an example.", ""

    decision, sql_hits, ret_hits = route(query)
    badge = f"**Router classified this as:** `{decision.upper()}`"
    if decision in ("sql", "both"):
        badge += "  -  this question has a counting aspect; exact statistics are on the **Data analyses** tab."

    if retriever == "Keyword (BM25)":
        raw = bm25_search(BM25, CHUNK_META, query, k=40)
    elif retriever == "Hybrid (RRF)":
        raw = hybrid_search(MODEL, VECTORS, CHUNK_META, BM25, query, k=40)
    else:
        raw = dense_search(MODEL, VECTORS, CHUNK_META, query, k=40)

    hits = _dedup_to_accidents(raw, k=5)
    if not hits:
        return badge, "No matching passages found. Try a more specific aviation term or switch retrievers."

    meta = _accident_meta([nid for _, nid, _ in hits])

    cards = []
    for i, (score, nid, text) in enumerate(hits, start=1):
        m = meta.get(nid, {})
        url = m.get("report_url")
        cite = f"[{nid}]({url})" if url else f"`{nid}`"
        context = _context_line(m)
        cause = m.get("probable_cause")
        cause = " ".join(str(cause).split())[:500] if cause else "(probable cause not available)"
        snippet = " ".join(str(text).split())[:240]
        card = (
            f"**{i}. {cite}**" + (f"  \u00b7  {context}" if context else "") + "\n\n"
            f"**Probable cause:** {cause}\n\n"
            f"**Matched passage** ({retriever}, score {score:.3f}): \u2026{snippet}\u2026"
        )
        cards.append(card)

    return badge, "\n\n---\n\n".join(cards)


def _make_chart(df, title):
    plt.close("all")
    cols = list(df.columns)
    labels = df[cols[0]].astype(str).tolist()
    values = list(df[cols[1]])
    fig, ax = plt.subplots(figsize=(7, max(3, 0.45 * len(labels))))
    y = list(range(len(labels)))
    ax.barh(y, values, color=ORANGE)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()              # first / largest row on top
    ax.set_xlabel(cols[1])
    ax.set_title(title)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return fig


def do_analysis(label):
    key = next(k for k, lab in list_analyses() if lab == label)
    sql, df = run_analysis(key)
    return sql, df, _make_chart(df, label)


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
        "### Question answering over 7,462 NTSB aviation accident reports\n"
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
