from app.crud import customer as customer_crud
from app.schemas.customer import CustomerCreate


def _make(db, **overrides):
    data = {"full_name": "Ada Lovelace", "email": "ada@example.com"}
    data.update(overrides)
    return customer_crud.create_customer(db, CustomerCreate(**data))


def test_create_customer_persists_and_returns_id(db):
    customer = _make(db)
    assert customer.id
    assert customer.full_name == "Ada Lovelace"
    assert customer.status == "active"  # schema default


def test_get_customer_by_id(db):
    created = _make(db)
    fetched = customer_crud.get_customer(db, created.id)
    assert fetched is not None
    assert fetched.email == "ada@example.com"


def test_get_customer_returns_none_for_missing_id(db):
    assert customer_crud.get_customer(db, "does-not-exist") is None


def test_list_customers_filters_by_status(db):
    _make(db, email="a@example.com", status="active")
    _make(db, email="b@example.com", full_name="Grace Hopper", status="at_risk")

    active_only = customer_crud.list_customers(db, status="active")
    assert {c.email for c in active_only} == {"a@example.com"}


def test_list_customers_query_matches_name_or_email(db):
    _make(db, email="daniel@example.com", full_name="Daniel Brooks")
    _make(db, email="ada@example.com", full_name="Ada Lovelace")

    by_name = customer_crud.list_customers(db, query="Daniel")
    assert {c.email for c in by_name} == {"daniel@example.com"}

    by_email = customer_crud.list_customers(db, query="ada@example.com")
    assert {c.email for c in by_email} == {"ada@example.com"}


def test_update_customer_only_changes_provided_fields(db):
    customer = _make(db)
    updated = customer_crud.update_customer(db, customer, {"phone": "+1-555-0100"})
    assert updated.phone == "+1-555-0100"
    assert updated.full_name == "Ada Lovelace"  # untouched


def test_get_customer_with_history_eager_loads_relationships(db):
    customer = _make(db)
    detail = customer_crud.get_customer_with_history(db, customer.id)
    assert detail is not None
    assert detail.orders == []
    assert detail.tickets == []
    assert detail.notes == []
