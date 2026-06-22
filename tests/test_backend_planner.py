from backend.app.analytics.chart_planner import plan_chart
from backend.app.analytics.query_planner import plan_sql
from backend.app.analytics.router import route_question
from backend.app.answer.composer import summarize_table
from chart_validator import validate_vega_lite_spec
from sql_guard import validate_sql


def test_route_question_promotes_sql_chart_request_to_chart():
    route = route_question("Show fatal accidents by phase of flight as a chart")
    assert route["route"] == "chart"
    assert "show" in route["chart_triggers"]


def test_route_question_landing_enroute_comparison_is_both():
    route = route_question("Are landing accidents more common than enroute accidents, but are they less fatal?")
    assert route["route"] == "both"


def test_route_question_top_states_is_chart():
    route = route_question("which states had the most reported incidents")
    assert route["route"] == "chart"


def test_plan_sql_for_fatal_phase_passes_guard():
    plan = plan_sql("Which phases of flight have the highest fatal accident counts?")
    validation = validate_sql(plan.sql)
    assert "broad_phaseof_flight" in validation.referenced_columns
    assert "fatal_injury_count" in validation.referenced_columns


def test_plan_sql_for_ohio_by_year_passes_guard():
    plan = plan_sql("Show accidents in Ohio by year")
    validation = validate_sql(plan.sql)
    assert validation.referenced_columns == ("event_year", "state")
    assert "Ohio" in validation.sql


def test_plan_sql_for_top_states_passes_guard():
    plan = plan_sql("which states had the most reported incidents")
    validation = validate_sql(plan.sql)
    assert validation.referenced_columns == ("state",)


def test_plan_sql_for_landing_enroute_comparison_passes_guard():
    plan = plan_sql("Are landing accidents more common than enroute accidents, but are they less fatal?")
    validation = validate_sql(plan.sql)
    assert "broad_phaseof_flight" in validation.referenced_columns
    assert "fatal_injury_count" in validation.referenced_columns


def test_plan_chart_returns_valid_vega_lite_spec():
    spec = plan_chart("Show accidents by year", ["year", "accidents"], title="Accidents by Year")
    validation = validate_vega_lite_spec(spec, ["year", "accidents"])
    assert validation.referenced_fields == ("accidents", "year")


def test_landing_enroute_summary_uses_frequency_and_fatal_rate():
    rows = [
        {"phase": "LANDING", "accidents": 2575, "fatal_accidents": 37, "fatal_rate": 0.0144},
        {"phase": "ENROUTE", "accidents": 1221, "fatal_accidents": 295, "fatal_rate": 0.2416},
    ]
    answer = summarize_table(
        "Are landing accidents more common than enroute accidents, but are they less fatal?",
        rows,
        "both",
    )
    assert "2575 vs 1221" in answer
    assert "1.4% vs 24.2%" in answer


def test_state_summary_names_top_state_and_top_five():
    rows = [
        {"state": "California", "accidents": 676},
        {"state": "Texas", "accidents": 646},
        {"state": "Florida", "accidents": 563},
        {"state": "Alaska", "accidents": 502},
        {"state": "Arizona", "accidents": 275},
    ]
    answer = summarize_table("which states had the most reported incidents", rows, "chart")
    assert "California had the most" in answer
    assert "California (676), Texas (646), Florida (563)" in answer


def test_landing_enroute_chart_prefers_fatal_rate_for_less_fatal_question():
    spec = plan_chart(
        "Are landing accidents more common than enroute accidents, but are they less fatal?",
        ["phase", "accidents", "fatal_accidents", "fatal_rate"],
    )
    assert spec["encoding"]["x"]["field"] == "fatal_rate"
    assert spec["encoding"]["y"]["field"] == "phase"
