from fastapi import APIRouter

from backend.app.data.db import run_validated_query
from backend.app.data.status import get_data_status
from schema_catalog import COLUMNS, TABLE_NAME

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


DATASET_SOURCE = {
    "name": "US NTSB aviation accident final reports",
    "provider": "NTSB, loaded from a public Zenodo dataset",
    "license": "Public domain (US government work)",
}

COVERAGE = {
    "start_year": 2016,
    "end_year": 2023,
    "known_gaps": [
        "2020 and 2021 are absent from this dataset.",
        "Recent years can be incomplete because NTSB final reports take time to publish.",
    ],
}

CAVEATS = [
    "The loaded corpus is not every aviation accident.",
    "Manufacturer names are normalized with a curated alias list (casing plus a few "
    "high-volume merges), not a complete entity-resolution solution.",
    "highest_injury_level was corrupted to nulls on load; fatal_injury_count > 0 is the "
    "reliable fatal signal.",
    "Multi-aircraft records can concatenate values in fields such as number_of_engines.",
]


@router.get("/dataset/card")
def dataset_card():
    status = get_data_status()
    return {
        "source": DATASET_SOURCE,
        "coverage": COVERAGE,
        "caveats": CAVEATS,
        "table": TABLE_NAME,
        "schema": [
            {"name": col.name, "dtype": col.dtype, "description": col.description}
            for col in COLUMNS
        ],
        "counts": {
            "accident_count": status.get("accident_count"),
            "tracked_source_count": status.get("tracked_source_count"),
        },
        "database": status.get("database"),
        "ready": status.get("ready", False),
        "latest_ingest": status.get("latest_ingest"),
    }


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
