# Evaluation Plan

The upgraded project needs evaluation beyond retrieval quality. The goal is not just "did the answer sound good" but whether the system chose the right route, executed safe SQL, rendered a valid chart, and cited real evidence.

## Evaluation Sets

Recommended files:

- `eval/router_cases.jsonl`
- `eval/sql_cases.jsonl`
- `eval/chart_cases.jsonl`
- `eval/retrieval_cases.jsonl`

## Router Evaluation

Score whether a question routes to:

- `sql`
- `retrieval`
- `chart`
- `both`

Examples:

- "fatal accidents by phase of flight" -> `chart`
- "why do pilots lose control in icing conditions" -> `retrieval`
- "are landing accidents more common but less fatal than enroute accidents" -> `both`

## SQL Evaluation

Score generated SQL for:

- Uses only the approved table.
- Uses only approved columns.
- Matches required filters.
- Uses the right aggregation.
- Passes `validate_sql`.
- Produces expected column names.

## Chart Evaluation

Score generated chart specs for:

- Valid Vega-Lite JSON.
- References only dataframe fields.
- Does not contain embedded data values.
- Uses an appropriate mark type.
- Passes `validate_vega_lite_spec`.

## Citation Evaluation

Score answer synthesis for:

- Every narrative claim links to a retrieved report or passage.
- Probable-cause claims are grounded in NTSB text.
- Statistical claims cite executed SQL instead of retrieved prose.
- Limitations are present when the question asks beyond the dataset.

## Regression Tests Already Added

The current suite includes:

- `tests/test_sql_guard.py`
- `tests/test_chart_validator.py`
- `tests/test_providers.py`

These tests protect the first production-grade guardrails while the app is refactored.

