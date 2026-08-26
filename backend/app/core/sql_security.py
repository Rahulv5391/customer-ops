import sqlglot
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlglot import exp

from app.core.exceptions import AppError

# The single canonical SQL validator (Architecture.md §8.1 - the reference
# had two divergent copies of this, only one actually wired in).
ALLOWED_TABLES = {
    "customers",
    "orders",
    "order_items",
    "tickets",
    "ticket_events",
    "agents",
    "escalations",
}
FORBIDDEN_TABLES = {"sqlite_master", "sqlite_sequence", "sqlite_temp_master"}
MAX_ROW_LIMIT = 50


class SQLSecurityViolation(AppError):
    """Raised when an LLM-generated SQL query fails allow-list validation."""


def validate_and_format_query(raw_sql: str) -> tuple[str, str | None]:
    """Parse, allow-list, and clamp an LLM-generated SQL string.

    The key defense is re-serializing the parsed AST back to SQL and
    returning THAT string rather than the original raw text — even if the
    model produced something unparseable-as-a-single-clean-SELECT, only
    what sqlglot actually parsed as the one Select AST is ever executed.

    Also returns the single table the query reads from, or None if the
    query joins/references more than one table (in which case a result
    row's `id` column would be ambiguous as to which entity it names).
    """
    clean_sql = raw_sql.strip().rstrip(";")

    try:
        parsed = [p for p in sqlglot.parse(clean_sql, read="sqlite") if p is not None]
    except Exception as exc:
        raise SQLSecurityViolation(f"SQL syntax error: {exc}") from exc

    if len(parsed) != 1:
        raise SQLSecurityViolation("Only a single SQL statement is permitted.")

    expression = parsed[0]
    if not isinstance(expression, exp.Select):
        raise SQLSecurityViolation("Only SELECT read-only queries are permitted.")

    tables = set()
    for table in expression.find_all(exp.Table):
        table_name = table.name.lower()
        if table_name in FORBIDDEN_TABLES:
            raise SQLSecurityViolation(f"Table '{table_name}' is not accessible.")
        if table_name not in ALLOWED_TABLES:
            raise SQLSecurityViolation(f"Table '{table_name}' is not in the allowed query schema.")
        tables.add(table_name)

    limit_clause = expression.args.get("limit")
    if limit_clause is not None:
        try:
            limit_value = int(limit_clause.expression.this)
        except (AttributeError, ValueError, TypeError):
            limit_value = MAX_ROW_LIMIT + 1  # force clamp on anything unparseable
        if limit_value > MAX_ROW_LIMIT:
            expression.set("limit", exp.Limit(expression=exp.Literal.number(MAX_ROW_LIMIT)))
    else:
        expression = expression.limit(MAX_ROW_LIMIT)

    single_table = next(iter(tables)) if len(tables) == 1 else None
    return expression.sql(dialect="sqlite"), single_table


def execute_safe_read_query(db: Session, raw_sql: str) -> tuple[list[str], list[tuple], str | None]:
    safe_sql, single_table = validate_and_format_query(raw_sql)
    result = db.execute(text(safe_sql))
    columns = list(result.keys())
    rows = result.fetchall()
    return columns, rows, single_table
