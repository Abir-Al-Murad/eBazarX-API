from pydantic import BaseModel, ConfigDict, Field, UUID4
from uuid import UUID
from decimal import Decimal
from typing import Optional, List
from datetime import datetime

class CartItemBase(BaseModel):
    variant_id: UUID4
    quantity: int = Field(..., gt=0)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)

class CartItemResponse(BaseModel):
    id: UUID
    variant_id: UUID
    product_id: UUID
    product_name: str
    price: Decimal
    quantity: int
    total: Decimal
    variant_attributes: Optional[dict] = None
    product_image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CartResponse(BaseModel):
    id: Optional[UUID] = None 
    items: List[CartItemResponse] = []
    subtotal: Decimal = Decimal(0)
    total_items: int = 0

    model_config = ConfigDict(from_attributes=True)