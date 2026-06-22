import re
from dataclasses import dataclass

from sqlglot import errors, exp, parse_one

from schema_catalog import SAFE_COLUMNS, TABLE_NAME


MAX_ROWS = 500
ALLOWED_FUNCTIONS = {
    "avg",
    "coalesce",
    "count",
    "date",
    "ifnull",
    "julianday",
    "lower",
    "max",
    "min",
    "nullif",
    "round",
    "strftime",
    "sum",
    "trim",
    "upper",
    "and",
    "case",
    "if",
}
MUTATION_RE = re.compile(
    r"\b(attach|alter|analyze|copy|create|delete|detach|drop|grant|insert|"
    r"listen|notify|pragma|reindex|replace|revoke|truncate|update|vacuum)\b",
    re.IGNORECASE,
)


class SqlValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SqlValidationResult:
    sql: str
    referenced_columns: tuple[str, ...]
    row_limit: int


def _strip_one_trailing_semicolon(sql):
    sql = sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].strip()
    if ";" in sql:
        raise SqlValidationError("SQL must contain a single SELECT statement.")
    return sql


def _basic_text_checks(sql):
    if not sql or not sql.strip():
        raise SqlValidationError("SQL is empty.")
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise SqlValidationError("SQL comments are not allowed.")
    sql = _strip_one_trailing_semicolon(sql)
    if not re.match(r"^\s*select\b", sql, re.IGNORECASE):
        raise SqlValidationError("Only SELECT statements are allowed.")
    if MUTATION_RE.search(sql):
        raise SqlValidationError("SQL contains a disallowed command.")
    return sql


def _parse_postgres(sql):
    try:
        return parse_one(sql, read="postgres")
    except errors.ParseError as exc:
        raise SqlValidationError(f"SQL failed validation: {exc}") from exc


def _select_aliases(ast):
    aliases = set()
    for expression in ast.expressions:
        alias = expression.alias
        if alias:
            aliases.add(alias)
    return aliases


def _validate_tables(ast):
    tables = list(ast.find_all(exp.Table))
    if not tables:
        raise SqlValidationError("SQL must read from the accidents table.")

    table_aliases = set()
    for table in tables:
        if table.name != TABLE_NAME or table.db or table.catalog:
            raise SqlValidationError("SQL may only read from the accidents table.")
        table_aliases.add(table.alias_or_name)
    table_aliases.add(TABLE_NAME)
    return table_aliases


def _validate_functions(ast):
    for function in ast.find_all(exp.Func):
        function_name = function.key.lower()
        if function_name not in ALLOWED_FUNCTIONS:
            raise SqlValidationError(f"Function {function_name!r} is not allowed.")


def _validate_stars(ast):
    for star in ast.find_all(exp.Star):
        if not isinstance(star.parent, exp.Count):
            raise SqlValidationError("SELECT * is not allowed.")


def _validate_columns(ast, table_aliases, output_aliases):
    referenced_columns = set()
    for column in ast.find_all(exp.Column):
        table = column.table
        name = column.name
        if name in output_aliases and not table:
            continue
        if table and table not in table_aliases:
            raise SqlValidationError(f"Unknown table qualifier {table!r}.")
        if name not in SAFE_COLUMNS:
            raise SqlValidationError(f"Column {name!r} is not in the safe schema.")
        referenced_columns.add(name)
    return referenced_columns


def _limit_value(ast):
    limit = ast.args.get("limit")
    if limit is None:
        return None
    expression = limit.args.get("expression")
    if expression is None or not isinstance(expression, exp.Literal) or expression.is_string:
        raise SqlValidationError("LIMIT must be a numeric literal.")
    try:
        return int(expression.this)
    except (TypeError, ValueError) as exc:
        raise SqlValidationError("LIMIT must be a numeric literal.") from exc


def _enforce_limit(ast, max_rows):
    existing_limit = _limit_value(ast)
    if existing_limit is not None:
        if existing_limit > max_rows:
            raise SqlValidationError(f"LIMIT may not exceed {max_rows}.")
        return ast, existing_limit
    ast = ast.copy().limit(max_rows)
    return ast, max_rows


def validate_sql(sql, *, max_rows=MAX_ROWS):
    """Validate Postgres-flavored LLM SQL before it can touch production data."""
    sql = _basic_text_checks(sql)
    ast = _parse_postgres(sql)
    if not isinstance(ast, exp.Select):
        raise SqlValidationError("Only SELECT statements are allowed.")
    if ast.args.get("with_"):
        raise SqlValidationError("CTEs are not allowed in generated SQL.")

    table_aliases = _validate_tables(ast)
    output_aliases = _select_aliases(ast)
    _validate_functions(ast)
    _validate_stars(ast)
    referenced_columns = _validate_columns(ast, table_aliases, output_aliases)
    limited_ast, row_limit = _enforce_limit(ast, max_rows)

    return SqlValidationResult(
        sql=limited_ast.sql(dialect="postgres"),
        referenced_columns=tuple(sorted(referenced_columns)),
        row_limit=row_limit,
    )
