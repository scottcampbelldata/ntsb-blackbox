from chart_validator import validate_vega_lite_spec


def _field(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def plan_chart(question, columns, *, title=None):
    columns = [str(col) for col in columns]
    x = _field(columns, ["year", "phase", "state", "weather", "make"])
    if "less fatal" in question.lower() or "fatal rate" in question.lower():
        y = _field(columns, ["fatal_rate", "fatal_accidents", "accidents"])
    else:
        y = _field(columns, ["fatal_accidents", "accidents", "fatal_rate"])
    if not x or not y:
        return None

    if x == "year" and "bar" not in question.lower():
        spec = {
            "mark": "line",
            "encoding": {
                "x": {"field": x, "type": "ordinal"},
                "y": {"field": y, "type": "quantitative"},
                "tooltip": [{"field": x}, {"field": y}],
            },
        }
    else:
        spec = {
            "mark": "bar",
            "encoding": {
                "x": {"field": y, "type": "quantitative"},
                "y": {"field": x, "type": "nominal", "sort": "-x"},
                "tooltip": [{"field": x}, {"field": y}],
            },
        }
    if title:
        spec["title"] = title
    validation = validate_vega_lite_spec(spec, columns)
    return validation.spec
