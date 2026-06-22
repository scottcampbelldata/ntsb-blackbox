import pytest

from sql_guard import SqlValidationError, validate_sql


def test_valid_select_gets_a_row_limit():
    result = validate_sql(
        """
        SELECT broad_phaseof_flight AS phase, COUNT(*) AS accidents
        FROM accidents
        WHERE fatal_injury_count > 0
        GROUP BY broad_phaseof_flight
        ORDER BY accidents DESC
        """
    )
    assert result.sql.endswith("LIMIT 500")
    assert result.referenced_columns == ("broad_phaseof_flight", "fatal_injury_count")


def test_existing_limit_is_preserved():
    result = validate_sql("SELECT event_year, COUNT(*) AS accidents FROM accidents GROUP BY event_year LIMIT 25")
    assert result.sql.endswith("LIMIT 25")
    assert result.row_limit == 25


def test_rejects_limit_above_cap():
    with pytest.raises(SqlValidationError):
        validate_sql("SELECT event_year FROM accidents LIMIT 10000")


def test_allows_safe_table_aliases():
    result = validate_sql("SELECT a.event_year FROM accidents AS a WHERE a.state = 'OH'")
    assert result.referenced_columns == ("event_year", "state")


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM accidents",
        "DROP TABLE accidents",
        "UPDATE accidents SET state = 'CA'",
        "PRAGMA table_info(accidents)",
        "WITH x AS (SELECT * FROM accidents) SELECT * FROM x",
    ],
)
def test_rejects_non_select_or_disallowed_commands(sql):
    with pytest.raises(SqlValidationError):
        validate_sql(sql)


def test_rejects_multiple_statements():
    with pytest.raises(SqlValidationError):
        validate_sql("SELECT event_year FROM accidents; SELECT state FROM accidents")


def test_rejects_comments():
    with pytest.raises(SqlValidationError):
        validate_sql("SELECT event_year FROM accidents -- hide something")


def test_rejects_unknown_table():
    with pytest.raises(SqlValidationError):
        validate_sql("SELECT event_year FROM users")


def test_rejects_unknown_column():
    with pytest.raises(SqlValidationError):
        validate_sql("SELECT password FROM accidents")


def test_rejects_select_star():
    with pytest.raises(SqlValidationError):
        validate_sql("SELECT * FROM accidents")


def test_rejects_unapproved_function():
    with pytest.raises(SqlValidationError):
        validate_sql("SELECT random() FROM accidents")
