from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrderItemBase(BaseModel):
    sku: str
    product_name: str
    quantity: int = 1
    unit_price: Decimal


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


class OrderBase(BaseModel):
    status: str = "placed"
    total_amount: Decimal
    currency: str = "USD"


class OrderCreate(OrderBase):
    customer_id: str
    items: list[OrderItemCreate] = []


class OrderUpdate(BaseModel):
    status: str | None = None


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    order_number: str
    placed_at: datetime
    updated_at: datetime


class OrderDetailResponse(OrderResponse):
    items: list[OrderItemResponse] = []
