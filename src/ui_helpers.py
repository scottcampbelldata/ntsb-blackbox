# src/ui_helpers.py
# ---------------------------------------------------------------------------
# Presentation helpers for the Gradio app, kept importable on their own so
# they can be unit-tested without loading the embedding model or the indexes.
#
# make_chart uses matplotlib's object-oriented Figure API rather than pyplot:
# pyplot keeps a process-wide figure registry that is not thread-safe, and
# Gradio runs event handlers on worker threads. A standalone Figure has no
# global state to corrupt and nothing to leak.
# ---------------------------------------------------------------------------

from matplotlib.figure import Figure

ORANGE = "#e8772e"


def make_chart(df, title):
    """Horizontal bar chart of a two-column dataframe (labels, values)."""
    cols = list(df.columns)
    labels = df[cols[0]].astype(str).tolist()
    values = list(df[cols[1]])
    fig = Figure(figsize=(7, max(3, 0.45 * len(labels))))
    ax = fig.subplots()
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


def router_badge(decision, sql_hits=(), ret_hits=()):
    """Markdown badge for the router's decision, naming the exact words that
    triggered it so the routing is as inspectable in the UI as in the code."""
    badge = f"**Router classified this as:** `{decision.upper()}`"
    triggers = ", ".join(f"'{w}'" for w in (*sql_hits, *ret_hits))
    if triggers:
        badge += f"  ·  triggered by {triggers}"
    else:
        badge += "  ·  no signal words matched; retrieval is the default"
    if decision in ("sql", "both"):
        badge += (
            "  -  this question has a counting aspect; exact statistics are "
            "on the **Data analyses** tab."
        )
    return badge


def context_line(m):
    """One compact line of accident context: make/model, year, place, severity."""
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
    if fatal > 0:
        bits.append(f"{int(fatal)} fatal")
    elif serious > 0:
        bits.append(f"{int(serious)} serious")
    return "  ·  ".join(bits)
