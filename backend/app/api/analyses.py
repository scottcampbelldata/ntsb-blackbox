from fastapi import APIRouter, HTTPException

from backend.app.data.db import run_validated_query
from chart_validator import validate_vega_lite_spec
from sql_tool import ANALYSES, list_analyses

router = APIRouter(prefix="/api")


def build_analysis_chart_spec(columns, *, title):
    """Build a validated Vega-Lite spec for a (category, value) analysis result,
    using the project chart convention: a line for a year category, otherwise a
    horizontal bar. Returns the validated spec, or None if the columns don't fit
    the (category, value) shape."""
    if len(columns) < 2:
        return None
    category, value = columns[0], columns[1]
    if category == "year":
        spec = {
            "mark": "line",
            "encoding": {
                "x": {"field": category, "type": "ordinal"},
                "y": {"field": value, "type": "quantitative"},
                "tooltip": [{"field": category}, {"field": value}],
            },
            "title": title,
        }
    else:
        spec = {
            "mark": "bar",
            "encoding": {
                "x": {"field": value, "type": "quantitative"},
                "y": {"field": category, "type": "nominal", "sort": "-x"},
                "tooltip": [{"field": category}, {"field": value}],
            },
            "title": title,
        }
    return validate_vega_lite_spec(spec, columns).spec


@router.get("/analyses")
def list_all_analyses():
    return {"analyses": [{"key": key, "label": label} for key, label in list_analyses()]}


@router.get("/analyses/{key}")
def run_analysis_endpoint(key: str):
    analysis = ANALYSES.get(key)
    if analysis is None:
        raise HTTPException(status_code=404, detail=f"Unknown analysis: {key}")
    result = run_validated_query(analysis["sql"])
    chart_spec = build_analysis_chart_spec(result.columns, title=analysis["label"])
    return {
        "key": key,
        "label": analysis["label"],
        "sql": result.sql,
        "columns": result.columns,
        "rows": result.rows,
        "chart_spec": chart_spec,
    }
