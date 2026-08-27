"""Covers the one call site in this codebase allowed to execute
LLM-generated SQL (RouterAgent._execute_read_path via
core/sql_security.py) - the allow-list is the actual trust boundary
between "the LLM wrote a query" and "that query touches the database",
so every rule here is security-relevant, not incidental correctness.
"""

import pytest

from app.core.sql_security import (
    MAX_ROW_LIMIT,
    SQLSecurityViolation,
    execute_safe_read_query,
    validate_and_format_query,
)
from app.models.customer import Customer


def test_allowed_table_passes():
    sql, table = validate_and_format_query("SELECT id, full_name FROM customers")
    assert table == "customers"
    assert "customers" in sql.lower()


def test_query_with_no_limit_gets_one_added():
    sql, _ = validate_and_format_query("SELECT id FROM customers")
    assert f"LIMIT {MAX_ROW_LIMIT}" in sql


def test_query_with_limit_under_max_is_untouched_value():
    sql, _ = validate_and_format_query("SELECT id FROM customers LIMIT 5")
    assert "LIMIT 5" in sql


def test_query_with_limit_over_max_gets_clamped():
    sql, _ = validate_and_format_query("SELECT id FROM customers LIMIT 999")
    assert f"LIMIT {MAX_ROW_LIMIT}" in sql
    assert "LIMIT 999" not in sql


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO customers (id) VALUES ('x')",
        "UPDATE customers SET full_name='x' WHERE id='1'",
        "DELETE FROM customers WHERE id='1'",
        "DROP TABLE customers",
    ],
)
def test_non_select_statements_are_rejected(statement):
    with pytest.raises(SQLSecurityViolation):
        validate_and_format_query(statement)


def test_multiple_statements_are_rejected():
    with pytest.raises(SQLSecurityViolation):
        validate_and_format_query("SELECT id FROM customers; SELECT id FROM agents")


def test_forbidden_table_is_rejected():
    with pytest.raises(SQLSecurityViolation):
        validate_and_format_query("SELECT * FROM sqlite_master")


def test_table_outside_allow_list_is_rejected():
    with pytest.raises(SQLSecurityViolation):
        validate_and_format_query("SELECT * FROM kb_documents")


def test_password_hash_column_is_not_blocked_by_name_but_agents_table_is_allowed():
    # agents.password_hash isn't in a separate forbidden-columns list - the
    # router prompt is responsible for never asking for it (Architecture.md
    # §5) - this test documents that the allow-list operates at the table
    # level, not column level, so it doesn't itself stop this query.
    sql, table = validate_and_format_query("SELECT password_hash FROM agents")
    assert table == "agents"


def test_syntax_error_is_rejected():
    with pytest.raises(SQLSecurityViolation):
        validate_and_format_query("SELEKT id FROM customers")


def test_join_across_two_allowed_tables_returns_no_single_table():
    sql, table = validate_and_format_query(
        "SELECT customers.id FROM customers JOIN orders ON orders.customer_id = customers.id"
    )
    assert table is None


def test_execute_safe_read_query_returns_real_rows(db):
    customer = Customer(full_name="Ada Lovelace", email="ada@example.com")
    db.add(customer)
    db.commit()

    columns, rows, table = execute_safe_read_query(db, "SELECT id, full_name FROM customers")
    assert table == "customers"
    assert columns == ["id", "full_name"]
    assert (customer.id, "Ada Lovelace") in rows
