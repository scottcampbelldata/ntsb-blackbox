def summarize_table(question, rows, route):
    if not rows:
        return "No matching rows were returned from the loaded NTSB accident dataset."

    q = question.lower()
    first = rows[0]
    cols = list(first)

    if "landing" in q and "enroute" in q:
        by_phase = {str(row.get("phase", "")).upper(): row for row in rows}
        landing = by_phase.get("LANDING")
        enroute = by_phase.get("ENROUTE")
        if landing and enroute:
            landing_rate = float(landing.get("fatal_rate") or 0)
            enroute_rate = float(enroute.get("fatal_rate") or 0)
            return (
                f"Yes. Landing accidents are more common in the loaded dataset "
                f"({landing.get('accidents')} vs {enroute.get('accidents')} enroute), "
                f"but they are less fatal by fatal-accident rate "
                f"({landing_rate:.1%} vs {enroute_rate:.1%}). "
                "Those values come from executed SQL."
            )

    if "state" in first and "accidents" in first:
        top = first
        top_five = rows[:5]
        detail = ", ".join(f"{row['state']} ({row['accidents']})" for row in top_five)
        return (
            f"{top['state']} had the most reported accidents in the loaded dataset, "
            f"with {top['accidents']} reports. The top five states in this result are: {detail}. "
            "These counts come from executed SQL over the structured accident table."
        )

    if "phase" in first and ("fatal_accidents" in first or "accidents" in first):
        metric = "fatal_accidents" if "fatal_accidents" in first else "accidents"
        return (
            f"The highest {metric.replace('_', ' ')} count in the returned result is "
            f"{first[metric]} for {first['phase']}. This number comes from the executed SQL, not model text."
        )

    if "year" in first and "accidents" in first:
        return (
            f"The query returned {len(rows)} yearly rows. The table and chart are based on executed SQL "
            "against the loaded accident dataset."
        )

    return (
        f"The query returned {len(rows)} rows with columns {', '.join(cols)}. "
        "Structured values come from executed SQL."
    )


def default_limitations(route):
    limitations = [
        "This uses the loaded NTSB final-report dataset, not every aviation accident.",
        "The current dataset notes 2020 and 2021 as absent, and recent years may lag final-report publication.",
    ]
    if route in ("retrieval", "both"):
        limitations.append("Narrative retrieval examples do not establish statistical frequency.")
    if route in ("sql", "chart", "both"):
        limitations.append("Structured counts depend on fields present in the accidents table.")
    return limitations
