# src/sql_tool.py
# ---------------------------------------------------------------------------
# Prebuilt, parameter-free SQL analyses over the structured accidents table.
# No text-to-SQL, no LLM: each analysis is a hand-written query that always
# runs and never hallucinates. Each result is returned ALONGSIDE the exact SQL
# that produced it, so every number on screen is traceable to a real query.
#
# Data lessons baked in:
#   - fatal_injury_count > 0 is the reliable fatal signal; highest_injury_level
#     was corrupted to nulls on load, so it is not used.
#   - Manufacturer names need normalization. UPPER() fixes casing
#     (CESSNA vs Cessna). MAKE_ALIASES below fixes naming variants that UPPER
#     cannot reach (ROBINSON vs ROBINSON HELICOPTER vs ROBINSON HELICOPTER
#     COMPANY). This is a CURATED list of high-volume, unambiguous merges, not
#     a complete entity-resolution solution; see README "Limitations".
# ---------------------------------------------------------------------------

import sqlite3

import pandas as pd

from paths import DB_PATH, require_file

# Curated manufacturer aliases: raw value (already uppercased) -> canonical name.
# Only obvious, high-count cases are merged. Extend deliberately; do not guess.
MAKE_ALIASES = {
    "ROBINSON HELICOPTER": "ROBINSON",
    "ROBINSON HELICOPTER COMPANY": "ROBINSON",
    "CIRRUS DESIGN CORP": "CIRRUS",
    "AIR TRACTOR INC": "AIR TRACTOR",
}


def _make_normalization_case(aliases=MAKE_ALIASES):
    """Build a CASE expression from MAKE_ALIASES so name variants collapse to
    one canonical make. Generated from the dict (single source of truth) and
    embedded in the query so the mapping is fully visible to anyone reading
    the SQL the demo shows."""
    for raw, canon in aliases.items():
        # the names are embedded in SQL string literals below; a quote would
        # silently break every query built from this expression
        if "'" in raw or "'" in canon:
            raise ValueError(
                f"alias may not contain a single quote: {raw!r} -> {canon!r}"
            )
    whens = "\n".join(
        f"               WHEN '{raw}' THEN '{canon}'"
        for raw, canon in aliases.items()
    )
    return (
        "CASE UPPER(make)\n"
        f"{whens}\n"
        "               ELSE UPPER(make)\n"
        "             END"
    )


_MAKE_EXPR = _make_normalization_case()

ANALYSES = {
    "accidents_by_year": {
        "label": "Accidents per year",
        "sql": """
            SELECT event_year AS year, COUNT(*) AS accidents
            FROM accidents
            WHERE event_year IS NOT NULL
            GROUP BY event_year
            ORDER BY event_year
        """,
    },
    "top_makes": {
        "label": "Top aircraft makes by accident count",
        # make names are normalized (casing + curated aliases) before grouping
        "sql": f"""
            SELECT
              {_MAKE_EXPR} AS make,
              COUNT(*) AS accidents
            FROM accidents
            WHERE make IS NOT NULL
            GROUP BY 1
            ORDER BY accidents DESC
            LIMIT 15
        """,
    },
    "fatal_breakdown": {
        "label": "Fatal vs non-fatal accidents",
        "sql": """
            SELECT
              CASE
                WHEN fatal_injury_count > 0 THEN 'fatal'
                WHEN fatal_injury_count = 0 THEN 'non-fatal'
                ELSE 'unknown'
              END AS outcome,
              COUNT(*) AS accidents
            FROM accidents
            GROUP BY outcome
            ORDER BY accidents DESC
        """,
    },
    "accidents_by_phase": {
        "label": "Accidents by phase of flight",
        "sql": """
            SELECT broad_phaseof_flight AS phase, COUNT(*) AS accidents
            FROM accidents
            WHERE broad_phaseof_flight IS NOT NULL
            GROUP BY broad_phaseof_flight
            ORDER BY accidents DESC
        """,
    },
    "fatal_by_phase": {
        "label": "Fatal accidents by phase of flight",
        "sql": """
            SELECT broad_phaseof_flight AS phase, COUNT(*) AS fatal_accidents
            FROM accidents
            WHERE fatal_injury_count > 0 AND broad_phaseof_flight IS NOT NULL
            GROUP BY broad_phaseof_flight
            ORDER BY fatal_accidents DESC
        """,
    },
    "accidents_by_state": {
        "label": "Accidents by state (top 15)",
        "sql": """
            SELECT state, COUNT(*) AS accidents
            FROM accidents
            WHERE state IS NOT NULL
            GROUP BY state
            ORDER BY accidents DESC
            LIMIT 15
        """,
    },
    "weather_breakdown": {
        "label": "Accidents by weather condition",
        "sql": """
            SELECT weather_condition AS weather, COUNT(*) AS accidents
            FROM accidents
            WHERE weather_condition IS NOT NULL
            GROUP BY weather_condition
            ORDER BY accidents DESC
        """,
    },
}


_KEY_BY_LABEL = {v["label"]: k for k, v in ANALYSES.items()}


def list_analyses():
    """Return [(key, human label), ...] for populating a dropdown."""
    return [(k, v["label"]) for k, v in ANALYSES.items()]


def analysis_key(label):
    """Map a display label back to its analysis key; None if unknown."""
    return _KEY_BY_LABEL.get(label)


def accident_count(con=None):
    """Total rows in the accidents table, so the app's headline figure comes
    from the data instead of a hardcoded constant."""
    own = con is None
    if own:
        require_file(DB_PATH, "SQLite accident database")
        con = sqlite3.connect(DB_PATH)
    try:
        return con.execute("SELECT COUNT(*) FROM accidents").fetchone()[0]
    finally:
        if own:
            con.close()


def run_analysis(key, con=None):
    """Run a named analysis. Returns (sql_text, dataframe)."""
    if key not in ANALYSES:
        raise KeyError(f"unknown analysis: {key}")
    sql = ANALYSES[key]["sql"].strip()
    own = con is None
    if own:
        require_file(DB_PATH, "SQLite accident database")
        con = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(sql, con)
    finally:
        if own:
            con.close()
    return sql, df


if __name__ == "__main__":
    require_file(DB_PATH, "SQLite accident database")
    con = sqlite3.connect(DB_PATH)
    for key, label in list_analyses():
        sql, df = run_analysis(key, con)
        print("\n" + "=" * 60)
        print(f"{label}   [{key}]")
        print("=" * 60)
        print(df.to_string(index=False))
    con.close()
