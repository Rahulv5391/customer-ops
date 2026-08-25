from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate, OrderUpdate


def get_order(db: Session, order_id: str) -> Order | None:
    return (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )


def list_orders_for_customer(db: Session, customer_id: str) -> list[Order]:
    return (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.customer_id == customer_id)
        .order_by(Order.placed_at.desc())
        .all()
    )


def create_order(db: Session, data: OrderCreate) -> Order:
    payload = data.model_dump(exclude={"items"})
    order = Order(**payload)
    order.items = [OrderItem(**item.model_dump()) for item in data.items]
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_order(db: Session, order: Order, updates: OrderUpdate) -> Order:
    for field, value in updates.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(order, field, value)
    db.commit()
    db.refresh(order)
    return order
