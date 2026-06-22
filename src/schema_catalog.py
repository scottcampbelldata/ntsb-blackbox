from dataclasses import dataclass


TABLE_NAME = "accidents"


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    dtype: str
    description: str
    groupable: bool = False
    filterable: bool = False
    aggregatable: bool = False
    chartable: bool = False
    citation: bool = False


COLUMNS = [
    ColumnSpec("ntsb_no", "TEXT", "NTSB accident identifier.", filterable=True, citation=True),
    ColumnSpec("event_type", "TEXT", "Event category from the source report.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("mkey", "INTEGER", "Source system numeric accident key.", filterable=True),
    ColumnSpec("event_date", "TIMESTAMP", "Accident event date.", filterable=True),
    ColumnSpec("city", "TEXT", "Event city.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("state", "TEXT", "US state or territory abbreviation.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("country", "TEXT", "Event country.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("report_no", "TEXT", "NTSB report number.", filterable=True, citation=True),
    ColumnSpec("has_safety_rec", "INTEGER", "Whether the report has a safety recommendation flag.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("mode", "TEXT", "Transportation mode.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("report_type", "TEXT", "Report type.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("highest_injury_level", "TEXT", "Highest injury level field; known to be sparse in this load.", groupable=True, filterable=True),
    ColumnSpec("fatal_injury_count", "REAL", "Fatal injuries recorded for the accident.", filterable=True, aggregatable=True, chartable=True),
    ColumnSpec("serious_injury_count", "REAL", "Serious injuries recorded for the accident.", filterable=True, aggregatable=True, chartable=True),
    ColumnSpec("minor_injury_count", "REAL", "Minor injuries recorded for the accident.", filterable=True, aggregatable=True, chartable=True),
    ColumnSpec("onboard_injury_count", "REAL", "Onboard injuries recorded for the accident.", filterable=True, aggregatable=True, chartable=True),
    ColumnSpec("on_ground_injury_count", "REAL", "On-ground injuries recorded for the accident.", filterable=True, aggregatable=True, chartable=True),
    ColumnSpec("probable_cause", "TEXT", "NTSB probable cause text; use for citations, not grouping.", filterable=True, citation=True),
    ColumnSpec("findings", "TEXT", "Structured/textual findings from the report.", filterable=True, citation=True),
    ColumnSpec("event_i_d", "REAL", "Source event ID.", filterable=True),
    ColumnSpec("latitude", "REAL", "Event latitude.", filterable=True, aggregatable=True, chartable=True),
    ColumnSpec("longitude", "REAL", "Event longitude.", filterable=True, aggregatable=True, chartable=True),
    ColumnSpec("make", "TEXT", "Aircraft make/manufacturer as reported.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("model", "TEXT", "Aircraft model as reported.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("air_craft_category", "TEXT", "Aircraft category.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("airport_i_d", "TEXT", "Airport identifier.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("airport_name", "TEXT", "Airport name.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("amateur_built", "TEXT", "Whether the aircraft was amateur-built.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("number_of_engines", "TEXT", "Number of engines; stored as text because multi-aircraft records can concatenate values.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("engine_type", "TEXT", "Engine type.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("scheduled", "TEXT", "Scheduled-service flag/category.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("purpose_of_flight", "TEXT", "Purpose of flight.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("f_a_r", "TEXT", "Applicable Federal Aviation Regulation part/category.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("air_craft_damage", "TEXT", "Aircraft damage severity.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("weather_condition", "TEXT", "Visual/instrument meteorological condition.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("operator", "TEXT", "Aircraft operator.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("broad_phaseof_flight", "TEXT", "Broad phase of flight.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("report_status", "TEXT", "Report status.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("most_recent_report_type", "TEXT", "Most recent report type.", groupable=True, filterable=True, chartable=True),
    ColumnSpec("docket_url", "TEXT", "NTSB docket URL.", citation=True),
    ColumnSpec("report_url", "TEXT", "NTSB report URL.", citation=True),
    ColumnSpec("event_year", "INTEGER", "Year extracted from event_date.", groupable=True, filterable=True, aggregatable=True, chartable=True),
]

_COLUMN_BY_NAME = {col.name: col for col in COLUMNS}
SAFE_COLUMNS = frozenset(_COLUMN_BY_NAME)


def column_names(*, groupable=None, filterable=None, aggregatable=None, chartable=None, citation=None):
    columns = COLUMNS
    flags = {
        "groupable": groupable,
        "filterable": filterable,
        "aggregatable": aggregatable,
        "chartable": chartable,
        "citation": citation,
    }
    for attr, expected in flags.items():
        if expected is not None:
            columns = [col for col in columns if getattr(col, attr) is expected]
    return [col.name for col in columns]


def get_column(name):
    return _COLUMN_BY_NAME.get(name)


def schema_prompt_context():
    lines = [f"Table: {TABLE_NAME}", "Columns:"]
    for col in COLUMNS:
        capabilities = []
        if col.groupable:
            capabilities.append("group")
        if col.filterable:
            capabilities.append("filter")
        if col.aggregatable:
            capabilities.append("aggregate")
        if col.chartable:
            capabilities.append("chart")
        if col.citation:
            capabilities.append("cite")
        suffix = f" ({', '.join(capabilities)})" if capabilities else ""
        lines.append(f"- {col.name} {col.dtype}: {col.description}{suffix}")
    return "\n".join(lines)
