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

# NTSB purpose-of-flight codes -> human-readable labels. The raw column stores
# cryptic codes (PERS, INST, ...); decoding them in the query keeps the result
# readable while leaving the mapping fully visible in the SQL the app shows.
PURPOSE_LABELS = {
    "PERS": "Personal",
    "INST": "Instructional",
    "AAPL": "Aerial application",
    "BUS": "Business",
    "POSI": "Positioning",
    "AOBV": "Aerial observation",
    "OWRK": "Other work use",
    "FLTS": "Flight test",
    "FERY": "Ferry",
    "SKYD": "Skydiving",
    "EXLD": "External load",
}

# Multi-aircraft accidents store concatenated values in a single field, e.g.
# purpose "PERS, PERS". They cannot be cleanly attributed to one group, so the
# grouped rate analyses exclude them with this predicate rather than letting them
# show up as spurious comma-joined categories.
_SINGLE_VALUE = "NOT LIKE '%, %'"


def _decode_case(input_sql, mapping, default_sql):
    """Build a CASE expression from a dict (the single source of truth) so the
    mapping is embedded in, and visible in, the SQL the app displays. `input_sql`
    and `default_sql` are raw SQL fragments (e.g. UPPER(make))."""
    for raw, canon in mapping.items():
        # the names are embedded in SQL string literals below; a quote would
        # silently break every query built from this expression
        if "'" in raw or "'" in canon:
            raise ValueError(
                f"mapping value may not contain a single quote: {raw!r} -> {canon!r}"
            )
    whens = "\n".join(
        f"               WHEN '{raw}' THEN '{canon}'"
        for raw, canon in mapping.items()
    )
    return (
        f"CASE {input_sql}\n"
        f"{whens}\n"
        f"               ELSE {default_sql}\n"
        "             END"
    )


def _make_normalization_case(aliases=MAKE_ALIASES):
    """Collapse make-name variants to one canonical make (casing + curated
    aliases). Thin wrapper over _decode_case kept for its callers and tests."""
    return _decode_case("UPPER(make)", aliases, "UPPER(make)")


_MAKE_EXPR = _make_normalization_case()
_PURPOSE_EXPR = _decode_case("UPPER(purpose_of_flight)", PURPOSE_LABELS,
                             "UPPER(purpose_of_flight)")

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
        "note": (
            "Read this as exposure, not risk. This is a raw count with no "
            "denominator: Cessna and Piper lead largely because they are the most "
            "numerous aircraft flying, not the most dangerous. Ranking risk would "
            "need fleet size or flight hours, which this dataset does not contain. "
            "For a risk signal that is available, see the fatality-rate analyses."
        ),
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
        "note": (
            "Exposure again, not danger. States with more flying (and more "
            "registered aircraft and airports) sit at the top; this chart does not "
            "normalize for that, so it largely tracks aviation activity rather than "
            "any state-level safety difference."
        ),
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
    # ----- Fatality-RATE analyses ----------------------------------------------
    # A raw count tells you where accidents happen; a fatality rate (the share of
    # accidents in a group that killed someone) tells you which conditions are
    # most lethal when an accident occurs. Each rate query reports the group size
    # too (so the reader can judge sample reliability), drops tiny buckets, and
    # excludes multi-aircraft concatenated values. chart_col tells the chart
    # builder to plot the rate rather than the count column beside it.
    "fatal_rate_by_phase": {
        "label": "Fatality rate by phase of flight",
        "chart_col": "fatal_rate_pct",
        "sql": """
            SELECT
              broad_phaseof_flight AS phase,
              COUNT(*) AS accidents,
              SUM(CASE WHEN fatal_injury_count > 0 THEN 1 ELSE 0 END) AS fatal,
              ROUND(100.0 * SUM(CASE WHEN fatal_injury_count > 0 THEN 1 ELSE 0 END)
                    / COUNT(*), 1) AS fatal_rate_pct
            FROM accidents
            WHERE broad_phaseof_flight IS NOT NULL
              AND broad_phaseof_flight <> 'Unknown'
            GROUP BY broad_phaseof_flight
            HAVING COUNT(*) >= 50
            ORDER BY fatal_rate_pct DESC
        """,
        "note": (
            "The inversion that matters. Landing produces the most accidents but "
            "kills in only about 1% of them, while maneuvering, initial climb, and "
            "enroute are fatal in roughly a quarter to a third of accidents. Most "
            "accidents happen on landing; the ones that kill happen with energy and "
            "altitude. Buckets under 50 accidents are dropped as too small to trust."
        ),
    },
    "fatal_rate_by_weather": {
        "label": "Fatality rate by weather condition",
        "chart_col": "fatal_rate_pct",
        "sql": """
            SELECT
              weather_condition AS weather,
              COUNT(*) AS accidents,
              SUM(CASE WHEN fatal_injury_count > 0 THEN 1 ELSE 0 END) AS fatal,
              ROUND(100.0 * SUM(CASE WHEN fatal_injury_count > 0 THEN 1 ELSE 0 END)
                    / COUNT(*), 1) AS fatal_rate_pct
            FROM accidents
            WHERE weather_condition IN ('VMC', 'IMC')
            GROUP BY weather_condition
            ORDER BY fatal_rate_pct DESC
        """,
        "note": (
            "Instrument conditions are roughly four times as lethal. An accident in "
            "IMC (cloud or low visibility, flown on instruments) is fatal about half "
            "the time, versus about 13% in VMC (clear visual conditions). Most flying "
            "is in VMC, which is why VMC still dominates the raw accident count "
            "despite the far lower rate."
        ),
    },
    "fatal_rate_by_purpose": {
        "label": "Fatality rate by purpose of flight",
        "chart_col": "fatal_rate_pct",
        "sql": f"""
            SELECT
              {_PURPOSE_EXPR} AS purpose,
              COUNT(*) AS accidents,
              SUM(CASE WHEN fatal_injury_count > 0 THEN 1 ELSE 0 END) AS fatal,
              ROUND(100.0 * SUM(CASE WHEN fatal_injury_count > 0 THEN 1 ELSE 0 END)
                    / COUNT(*), 1) AS fatal_rate_pct
            FROM accidents
            WHERE purpose_of_flight IS NOT NULL
              AND purpose_of_flight {_SINGLE_VALUE}
            GROUP BY 1
            HAVING COUNT(*) >= 50
            ORDER BY fatal_rate_pct DESC
        """,
        "note": (
            "Instructional flying is the safest common category, at about half the "
            "personal-flight fatality rate, consistent with a trained instructor "
            "aboard, a controlled environment, and conservative profiles. Codes are "
            "decoded in the query; buckets under 50 accidents are dropped."
        ),
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
