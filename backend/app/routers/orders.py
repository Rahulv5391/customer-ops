from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import customer as customer_crud
from app.crud import order as order_crud
from app.models.agent import SupportAgent
from app.schemas.order import OrderDetailResponse, OrderResponse, OrderUpdate
from app.services.auth_service import get_current_agent

router = APIRouter(tags=["orders"])


@router.get("/customers/{customer_id}/orders", response_model=list[OrderDetailResponse])
def list_orders_for_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    if not customer_crud.get_customer(db, customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    return order_crud.list_orders_for_customer(db, customer_id)


@router.get("/orders/{order_id}", response_model=OrderDetailResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    order = order_crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/orders/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: str,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    order = order_crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_crud.update_order(db, order, payload)
