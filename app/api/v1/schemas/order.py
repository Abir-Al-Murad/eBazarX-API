from pydantic import BaseModel, ConfigDict, Field, UUID4
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from app.infrastructure.database.models import OrderStatus, PaymentStatus

# ----- Order Item -----
class OrderItemBase(BaseModel):
    variant_id: UUID4
    quantity: int = Field(..., gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(BaseModel):
    id: UUID
    product_name_at_time: str
    price_at_time: Decimal
    quantity: int
    size_at_time: Optional[str]
    color_at_time: Optional[str]
    status: OrderStatus
    product_id: UUID
    variant_id: UUID
    seller_id: UUID
    product_image: Optional[str] = Field(None, alias="product_image_at_time")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ----- Order -----
class OrderBase(BaseModel):
    address_id: UUID4

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]
    coupon_code: Optional[str] = None
    notes: Optional[str] = None

class OrderUpdateStatus(BaseModel):
    status: OrderStatus

class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    address_id: UUID
    subtotal: Decimal
    shipping_fee: Decimal
    tax: Decimal
    discount_amount: Decimal
    grand_total: Decimal
    payment_method: Optional[str]
    payment_status: PaymentStatus
    order_status: OrderStatus
    tracking_number: Optional[str]
    estimated_delivery: Optional[datetime]
    notes: Optional[str]
    coupon_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)