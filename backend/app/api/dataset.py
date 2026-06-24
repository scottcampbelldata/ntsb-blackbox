from fastapi import APIRouter

from backend.app.data.db import run_validated_query

router = APIRouter(prefix="/api")

# One validated query produces every KPI. SUM(CASE ...) counts fatal accidents
# (fatal_injury_count > 0 is the reliable fatal signal in this dataset).
KPI_SQL = """
    SELECT
      COUNT(*) AS accident_count,
      SUM(CASE WHEN fatal_injury_count > 0 THEN 1 ELSE 0 END) AS fatal_count,
      MIN(event_year) AS min_year,
      MAX(event_year) AS max_year,
      COUNT(DISTINCT make) AS distinct_makes
    FROM accidents
"""


@router.get("/dataset")
def dataset_kpis():
    result = run_validated_query(KPI_SQL)
    row = result.rows[0]
    return {
        "accident_count": int(row["accident_count"] or 0),
        "fatal_count": int(row["fatal_count"] or 0),
        "min_year": int(row["min_year"]) if row["min_year"] is not None else None,
        "max_year": int(row["max_year"]) if row["max_year"] is not None else None,
        "distinct_makes": int(row["distinct_makes"] or 0),
    }
