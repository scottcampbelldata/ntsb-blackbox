import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from ui_helpers import context_line, make_chart, router_badge


def test_make_chart_never_touches_the_global_pyplot_registry():
    df = pd.DataFrame({"phase": ["landing", "takeoff"], "accidents": [10, 4]})
    fig = make_chart(df, "Accidents by phase")
    assert isinstance(fig, Figure)
    # pyplot's registry is process-global and not thread-safe; the chart must
    # be a standalone Figure that never registers there
    assert plt.get_fignums() == []


def test_make_chart_labels_come_from_the_dataframe():
    df = pd.DataFrame({"phase": ["landing", "takeoff", "cruise"], "accidents": [10, 4, 2]})
    fig = make_chart(df, "a title")
    ax = fig.axes[0]
    assert ax.get_title() == "a title"
    assert ax.get_xlabel() == "accidents"
    assert len(ax.patches) == 3


def test_context_line_full_meta():
    m = {
        "make": "CESSNA", "model": "172", "event_year": 2019,
        "city": "Anchorage", "state": "AK",
        "fatal_injury_count": 2, "serious_injury_count": 1,
    }
    assert context_line(m) == "Cessna 172  ·  2019  ·  Anchorage, AK  ·  2 fatal"


def test_context_line_serious_only_when_no_fatalities():
    m = {"fatal_injury_count": 0, "serious_injury_count": 1}
    assert context_line(m) == "1 serious"


def test_context_line_handles_missing_fields():
    assert context_line({}) == ""
    assert context_line({"make": "PIPER"}) == "Piper"


def test_router_badge_names_the_decision_and_its_triggers():
    badge = router_badge("sql", ["how many"], [])
    assert "`SQL`" in badge
    assert "'how many'" in badge
    assert "Data analyses" in badge


def test_router_badge_shows_triggers_from_both_sides():
    badge = router_badge("both", ["how many"], ["why"])
    assert "'how many'" in badge
    assert "'why'" in badge


def test_router_badge_retrieval_without_triggers_says_it_was_the_default():
    badge = router_badge("retrieval", [], [])
    assert "`RETRIEVAL`" in badge
    assert "default" in badge


def test_router_badge_pure_retrieval_does_not_point_at_the_sql_tab():
    badge = router_badge("retrieval", [], ["why"])
    assert "Data analyses" not in badge
