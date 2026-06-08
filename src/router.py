# src/router.py
# ---------------------------------------------------------------------------
# The top-level router: decides whether a question should be answered from the
# STRUCTURED table (SQL), the DOCUMENT narratives (retrieval), or BOTH. This is
# the spine of the project:
#   "how many fatal accidents in 2019"            -> counting        -> SQL
#   "what tends to go wrong in icing accidents"   -> explanation     -> retrieval
#   "what were the most common phases of flight,
#    and what goes wrong in the top one"          -> count + explain -> both
#
# This is a v1 RULE-BASED router: transparent, cheap, no LLM, and every
# decision is inspectable (it returns the exact words that triggered it). It is
# also deliberately brittle. See the LIMITATIONS notes at the bottom for where
# it breaks. The planned upgrade is an LLM classifier, which we can later
# evaluate against this one for routing accuracy.
#
# Run from the project root:   python src/router.py
# ---------------------------------------------------------------------------

import re

# Phrases that signal a COUNTING or AGGREGATION question -> SQL
SQL_SIGNALS = [
    r"\bhow many\b", r"\bhow much\b", r"\bnumber of\b", r"\bcount\b",
    r"\baverage\b", r"\bmean\b", r"\bmedian\b", r"\btotal\b", r"\bsum\b",
    r"\bmost\b", r"\bleast\b", r"\bhighest\b", r"\blowest\b", r"\btop\b", r"\bfewest\b",
    r"\bper year\b", r"\bby year\b", r"\beach year\b", r"\bover time\b", r"\btrend\b",
    r"\brank\b", r"\bcompare\b", r"\bbreakdown\b", r"\bpercentage\b", r"\brate of\b",
]

# Phrases that signal an EXPLANATION or NARRATIVE question -> retrieval
RETRIEVAL_SIGNALS = [
    r"\bwhy\b", r"\bhow did\b", r"\bwhat happened\b", r"\bdescribe\b", r"\bexplain\b",
    r"\bwhat factors\b", r"\bcontributing\b", r"\bwhat (goes|went) wrong\b",
    r"\btends? to\b", r"\bcommonly\b", r"\busually\b", r"\bexamples? of\b",
    r"\bsequence of events\b", r"\blessons\b", r"\bstories\b",
]


def _matches(text, patterns):
    found = []
    for p in patterns:
        m = re.search(p, text)
        if m:
            found.append(m.group(0).strip())
    return found


def route(query):
    """Return (decision, sql_triggers, retrieval_triggers).
    decision is one of 'sql', 'retrieval', 'both'."""
    q = query.lower()
    sql_hits = _matches(q, SQL_SIGNALS)
    ret_hits = _matches(q, RETRIEVAL_SIGNALS)

    if sql_hits and ret_hits:
        decision = "both"
    elif sql_hits:
        decision = "sql"
    elif ret_hits:
        decision = "retrieval"
    else:
        # Default: when nothing signals counting, lean on the documents. An
        # open-ended question is usually better served by reading reports than
        # by guessing at a SQL query against fields that may not exist.
        decision = "retrieval"
    return decision, sql_hits, ret_hits


if __name__ == "__main__":
    print("Router demo. Type a question to see how it routes. Type quit to exit.\n")
    while True:
        try:
            query = input("route> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            break
        decision, sql_hits, ret_hits = route(query)
        print(f"  ROUTE: {decision.upper()}")
        if sql_hits:
            print(f"  sql signals:       {sql_hits}")
        if ret_hits:
            print(f"  retrieval signals: {ret_hits}")
        if not sql_hits and not ret_hits:
            print("  (no signals matched; defaulted to retrieval)")
        print()

# ---------------------------------------------------------------------------
# LIMITATIONS (the honest part, for the decision log):
# 1. "How many accidents were caused by spatial disorientation" routes to SQL
#    because of "how many", but disorientation is not a structured column, it
#    lives in the narrative text. A rule router cannot know that. An LLM that
#    sees the schema can.
# 2. Pure filter-and-list questions ("show me accidents in California") have no
#    aggregation word, so they default to retrieval even though they are really
#    SQL (WHERE state = 'California'). Known gap.
# 3. The word "common" is ambiguous: "most common make" is SQL (group + count),
#    but "common causes of icing" is retrieval. Keywords cannot resolve that.
# These are exactly the cases that justify the LLM-classifier upgrade.
# ---------------------------------------------------------------------------
