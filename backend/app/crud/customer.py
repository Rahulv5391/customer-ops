from sqlalchemy.orm import Session, selectinload

from app.models.customer import Customer
from app.models.order import Order
from app.models.ticket import Ticket
from app.schemas.customer import CustomerCreate


def get_customer(db: Session, customer_id: str) -> Customer | None:
    return db.get(Customer, customer_id)


def get_customer_with_history(db: Session, customer_id: str) -> Customer | None:
    return (
        db.query(Customer)
        .options(
            selectinload(Customer.orders).selectinload(Order.items),
            selectinload(Customer.tickets).selectinload(Ticket.events),
            selectinload(Customer.notes),
        )
        .filter(Customer.id == customer_id)
        .first()
    )


def list_customers(
    db: Session,
    query: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Customer]:
    q = db.query(Customer)
    if status:
        q = q.filter(Customer.status == status)
    if query:
        like = f"%{query}%"
        q = q.filter(
            (Customer.full_name.ilike(like))
            | (Customer.email.ilike(like))
            | (Customer.id == query)
        )
    return q.order_by(Customer.created_at.desc()).offset(offset).limit(limit).all()


def create_customer(db: Session, data: CustomerCreate) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, customer: Customer, updates: dict) -> Customer:
    for field, value in updates.items():
        if value is not None:
            setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer
