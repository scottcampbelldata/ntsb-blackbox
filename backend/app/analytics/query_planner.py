import re
from dataclasses import dataclass


class QueryPlanningError(ValueError):
    pass


@dataclass(frozen=True)
class QueryPlan:
    sql: str
    title: str
    chart: bool = False
    confidence: float = 0.7
    notes: tuple[str, ...] = ()


STATES = {
    "alabama": ("Alabama", "AL"), "alaska": ("Alaska", "AK"), "arizona": ("Arizona", "AZ"),
    "arkansas": ("Arkansas", "AR"), "california": ("California", "CA"), "colorado": ("Colorado", "CO"),
    "connecticut": ("Connecticut", "CT"), "delaware": ("Delaware", "DE"), "florida": ("Florida", "FL"),
    "georgia": ("Georgia", "GA"), "hawaii": ("Hawaii", "HI"), "idaho": ("Idaho", "ID"),
    "illinois": ("Illinois", "IL"), "indiana": ("Indiana", "IN"), "iowa": ("Iowa", "IA"),
    "kansas": ("Kansas", "KS"), "kentucky": ("Kentucky", "KY"), "louisiana": ("Louisiana", "LA"),
    "maine": ("Maine", "ME"), "maryland": ("Maryland", "MD"), "massachusetts": ("Massachusetts", "MA"),
    "michigan": ("Michigan", "MI"), "minnesota": ("Minnesota", "MN"), "mississippi": ("Mississippi", "MS"),
    "missouri": ("Missouri", "MO"), "montana": ("Montana", "MT"), "nebraska": ("Nebraska", "NE"),
    "nevada": ("Nevada", "NV"), "new hampshire": ("New Hampshire", "NH"), "new jersey": ("New Jersey", "NJ"),
    "new mexico": ("New Mexico", "NM"), "new york": ("New York", "NY"), "north carolina": ("North Carolina", "NC"),
    "north dakota": ("North Dakota", "ND"), "ohio": ("Ohio", "OH"), "oklahoma": ("Oklahoma", "OK"),
    "oregon": ("Oregon", "OR"), "pennsylvania": ("Pennsylvania", "PA"), "rhode island": ("Rhode Island", "RI"),
    "south carolina": ("South Carolina", "SC"), "south dakota": ("South Dakota", "SD"), "tennessee": ("Tennessee", "TN"),
    "texas": ("Texas", "TX"), "utah": ("Utah", "UT"), "vermont": ("Vermont", "VT"),
    "virginia": ("Virginia", "VA"), "washington": ("Washington", "WA"), "west virginia": ("West Virginia", "WV"),
    "wisconsin": ("Wisconsin", "WI"), "wyoming": ("Wyoming", "WY"),
}


def _state_name(question):
    abbreviation_to_name = {abbr: name for name, abbr in STATES.values()}
    states = {
        state_name.lower(): state_name
        for state_name, _abbr in STATES.values()
    }
    q = question.lower()
    for name, state_name in states.items():
        if re.search(rf"\b{re.escape(name)}\b", q):
            return state_name
    match = re.search(r"\b[A-Z]{2}\b", question)
    if match:
        return abbreviation_to_name.get(match.group(0))
    return None


def plan_sql(question, *, wants_chart=False):
    q = question.lower()

    if "landing" in q and ("enroute" in q or "en route" in q):
        return QueryPlan(
            title="Landing vs Enroute Frequency and Fatality",
            chart=wants_chart,
            confidence=0.88,
            notes=("Compares frequency and severity for two broad phases of flight.",),
            sql="""
                SELECT
                  UPPER(broad_phaseof_flight) AS phase,
                  COUNT(*) AS accidents,
                  SUM(CASE WHEN fatal_injury_count > 0 THEN 1 ELSE 0 END) AS fatal_accidents,
                  ROUND(
                    SUM(CASE WHEN fatal_injury_count > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*),
                    4
                  ) AS fatal_rate
                FROM accidents
                WHERE UPPER(broad_phaseof_flight) IN ('LANDING', 'ENROUTE')
                GROUP BY UPPER(broad_phaseof_flight)
                ORDER BY accidents DESC
            """,
        )

    if "phase" in q and ("fatal" in q or "fatality" in q):
        return QueryPlan(
            title="Fatal Accidents by Phase of Flight",
            chart=True,
            confidence=0.9,
            sql="""
                SELECT broad_phaseof_flight AS phase, COUNT(*) AS fatal_accidents
                FROM accidents
                WHERE fatal_injury_count > 0 AND broad_phaseof_flight IS NOT NULL
                GROUP BY broad_phaseof_flight
                ORDER BY fatal_accidents DESC
            """,
        )

    state = _state_name(question)
    if state and "year" in q:
        return QueryPlan(
            title=f"Accidents in {state} by Year",
            chart=True,
            confidence=0.86,
            sql=f"""
                SELECT event_year AS year, COUNT(*) AS accidents
                FROM accidents
                WHERE UPPER(state) = UPPER('{state}') AND event_year IS NOT NULL
                GROUP BY event_year
                ORDER BY event_year
            """,
        )

    if ("state" in q or "states" in q) and re.search(r"\b(most|highest|top|reported|incidents?|accidents?|count)\b", q):
        return QueryPlan(
            title="Top States by Reported Accidents",
            chart=True,
            confidence=0.84,
            sql="""
                SELECT state, COUNT(*) AS accidents
                FROM accidents
                WHERE state IS NOT NULL
                GROUP BY state
                ORDER BY accidents DESC
                LIMIT 15
            """,
        )

    if "year" in q or "over time" in q or "trend" in q:
        return QueryPlan(
            title="Accidents by Year",
            chart=True,
            confidence=0.82,
            sql="""
                SELECT event_year AS year, COUNT(*) AS accidents
                FROM accidents
                WHERE event_year IS NOT NULL
                GROUP BY event_year
                ORDER BY event_year
            """,
        )

    if "weather" in q:
        return QueryPlan(
            title="Accidents by Weather Condition",
            chart=True,
            confidence=0.78,
            sql="""
                SELECT weather_condition AS weather, COUNT(*) AS accidents
                FROM accidents
                WHERE weather_condition IS NOT NULL
                GROUP BY weather_condition
                ORDER BY accidents DESC
            """,
        )

    if "make" in q or "manufacturer" in q:
        return QueryPlan(
            title="Top Aircraft Makes by Accident Count",
            chart=True,
            confidence=0.75,
            sql="""
                SELECT UPPER(make) AS make, COUNT(*) AS accidents
                FROM accidents
                WHERE make IS NOT NULL
                GROUP BY UPPER(make)
                ORDER BY accidents DESC
            """,
        )

    if "phase" in q:
        return QueryPlan(
            title="Accidents by Phase of Flight",
            chart=True,
            confidence=0.78,
            sql="""
                SELECT broad_phaseof_flight AS phase, COUNT(*) AS accidents
                FROM accidents
                WHERE broad_phaseof_flight IS NOT NULL
                GROUP BY broad_phaseof_flight
                ORDER BY accidents DESC
            """,
        )

    raise QueryPlanningError("No deterministic SQL plan matched this question.")
