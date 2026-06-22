import re

from router import route as baseline_route


CHART_SIGNALS = [
    r"\bchart\b",
    r"\bgraph\b",
    r"\bplot\b",
    r"\bbar\b",
    r"\bline\b",
    r"\bvisuali[sz]e\b",
    r"\bshow\b",
]

ANALYTICAL_TERMS = [
    "accident",
    "accidents",
    "incident",
    "incidents",
    "fatal",
    "fatality",
    "count",
    "counts",
    "phase",
    "year",
    "state",
    "states",
    "weather",
    "make",
    "manufacturer",
    "compare",
]


def route_question(question):
    decision, sql_hits, retrieval_hits = baseline_route(question)
    chart_hits = []
    q = question.lower()
    for pattern in CHART_SIGNALS:
        match = re.search(pattern, q)
        if match:
            chart_hits.append(match.group(0))

    looks_analytical = any(term in q for term in ANALYTICAL_TERMS)

    if "landing" in q and ("enroute" in q or "en route" in q):
        decision = "both"
    elif ("state" in q or "states" in q) and re.search(r"\b(most|highest|top|reported|incidents?|accidents?)\b", q):
        decision = "chart"

    if chart_hits and decision == "retrieval" and looks_analytical:
        decision = "chart"
    elif chart_hits and decision == "sql":
        decision = "chart"
    elif chart_hits and decision == "both":
        decision = "both"

    return {
        "route": decision,
        "sql_triggers": sql_hits,
        "retrieval_triggers": retrieval_hits,
        "chart_triggers": chart_hits,
    }
