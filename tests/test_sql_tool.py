import sqlite3

import pytest

from paths import DB_PATH
from sql_tool import (
    ANALYSES,
    MAKE_ALIASES,
    _make_normalization_case,
    accident_count,
    analysis_key,
    list_analyses,
    run_analysis,
)


def test_labels_are_unique():
    labels = [label for _, label in list_analyses()]
    assert len(labels) == len(set(labels))


def test_analysis_key_round_trips_every_label():
    for key, label in list_analyses():
        assert analysis_key(label) == key


def test_analysis_key_unknown_label_returns_none():
    assert analysis_key("not a real analysis") is None


def test_alias_containing_a_quote_is_rejected():
    # alias values are embedded in SQL string literals; a quote would silently
    # break every query built from the CASE expression
    with pytest.raises(ValueError):
        _make_normalization_case({"O'BRIEN AVIATION": "OBRIEN"})


def test_shipped_aliases_are_quote_free():
    _make_normalization_case(MAKE_ALIASES)  # must not raise


def test_unknown_analysis_key_raises():
    with pytest.raises(KeyError):
        run_analysis("nope")


def test_accident_count_counts_table_rows():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE accidents (ntsb_no TEXT)")
    con.executemany("INSERT INTO accidents VALUES (?)", [("A",), ("B",), ("C",)])
    assert accident_count(con) == 3


needs_db = pytest.mark.skipif(not DB_PATH.exists(), reason="local database not built")


@needs_db
@pytest.mark.parametrize("key", sorted(ANALYSES))
def test_every_analysis_runs_and_returns_rows(key):
    sql, df = run_analysis(key)
    assert sql.strip().upper().startswith("SELECT")
    # count analyses are (category, value); rate analyses carry extra count
    # columns alongside the rate, so the contract is "at least two columns".
    assert df.shape[1] >= 2
    assert len(df) > 0


@needs_db
@pytest.mark.parametrize("key", sorted(ANALYSES))
def test_declared_chart_col_exists_in_result(key):
    chart_col = ANALYSES[key].get("chart_col")
    if chart_col is not None:
        _sql, df = run_analysis(key)
        assert chart_col in df.columns


@needs_db
@pytest.mark.parametrize("key", sorted(k for k in ANALYSES if k.startswith("fatal_rate")))
def test_rate_analyses_are_valid_percentages(key):
    _sql, df = run_analysis(key)
    assert df["fatal_rate_pct"].between(0, 100).all()
    assert (df["fatal"] <= df["accidents"]).all()


@needs_db
def test_purpose_codes_are_decoded_and_concatenations_excluded():
    _sql, df = run_analysis("fatal_rate_by_purpose")
    purposes = set(df["purpose"])
    assert "Personal" in purposes        # PERS decoded
    assert "PERS" not in purposes
    assert not any(", " in str(p) for p in purposes)  # no multi-aircraft rows
