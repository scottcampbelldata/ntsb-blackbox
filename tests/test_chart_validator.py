import pytest

from chart_validator import ChartValidationError, validate_vega_lite_spec


def test_valid_bar_chart_references_dataframe_fields():
    spec = {
        "mark": "bar",
        "encoding": {
            "x": {"field": "phase", "type": "nominal"},
            "y": {"field": "fatal_accidents", "type": "quantitative"},
            "tooltip": [
                {"field": "phase", "type": "nominal"},
                {"field": "fatal_accidents", "type": "quantitative"},
            ],
        },
    }
    result = validate_vega_lite_spec(spec, ["phase", "fatal_accidents"])
    assert result.referenced_fields == ("fatal_accidents", "phase")


def test_rejects_specs_with_embedded_data():
    spec = {
        "data": {"values": [{"phase": "landing", "accidents": 10}]},
        "mark": "bar",
        "encoding": {
            "x": {"field": "phase"},
            "y": {"field": "accidents"},
        },
    }
    with pytest.raises(ChartValidationError):
        validate_vega_lite_spec(spec, ["phase", "accidents"])


def test_rejects_missing_dataframe_field():
    spec = {
        "mark": "bar",
        "encoding": {
            "x": {"field": "phase"},
            "y": {"field": "invented_count"},
        },
    }
    with pytest.raises(ChartValidationError):
        validate_vega_lite_spec(spec, ["phase", "accidents"])


def test_rejects_transform_calculations():
    spec = {
        "mark": "bar",
        "transform": [{"calculate": "datum.accidents * 2", "as": "fake"}],
        "encoding": {
            "x": {"field": "phase"},
            "y": {"field": "fake"},
        },
    }
    with pytest.raises(ChartValidationError):
        validate_vega_lite_spec(spec, ["phase", "accidents"])


def test_rejects_unsupported_mark():
    spec = {
        "mark": "text",
        "encoding": {
            "x": {"field": "phase"},
            "y": {"field": "accidents"},
        },
    }
    with pytest.raises(ChartValidationError):
        validate_vega_lite_spec(spec, ["phase", "accidents"])
