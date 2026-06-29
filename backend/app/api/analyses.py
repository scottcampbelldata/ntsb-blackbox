from decimal import Decimal

from fastapi import APIRouter, HTTPException

from backend.app.data.db import run_validated_query
from chart_validator import validate_vega_lite_spec
from sql_tool import ANALYSES, list_analyses

router = APIRouter(prefix="/api")


def _jsonable_rows(rows: list[dict]) -> list[dict]:
    """Coerce Postgres numeric/Decimal values to float so the response is plain
    JSON. Postgres returns ROUND() as Decimal (the rate analyses hit this); the
    SQLite path already returns float, so this also keeps the two backends'
    output identical. Counts stay int; text/None pass through untouched."""
    return [
        {k: (float(v) if isinstance(v, Decimal) else v) for k, v in row.items()}
        for row in rows
    ]


def build_analysis_chart_spec(
    columns: list[str], *, title: str, value_col: str | None = None
) -> dict | None:
    """Build a validated Vega-Lite spec for a (category, value) analysis result,
    using the project chart convention: a line for a year category, otherwise a
    horizontal bar. Returns the validated spec, or None if the columns don't fit
    the (category, value) shape.

    The value plotted is `value_col` when given and present (rate analyses carry
    extra count columns and want the rate charted, not the count beside it);
    otherwise it defaults to the second column."""
    if len(columns) < 2:
        return None
    category = columns[0]
    value = value_col if value_col in columns else columns[1]
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
    chart_spec = build_analysis_chart_spec(
        result.columns, title=analysis["label"], value_col=analysis.get("chart_col")
    )
    return {
        "key": key,
        "label": analysis["label"],
        "sql": result.sql,
        "columns": result.columns,
        "rows": _jsonable_rows(result.rows),
        "chart_spec": chart_spec,
        "note": analysis.get("note"),
    }
