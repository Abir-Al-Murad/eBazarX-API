from pydantic import BaseModel, ConfigDict, UUID4
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

class WishlistItemCreate(BaseModel):
    variant_id: UUID4

class WishlistItemResponse(BaseModel):
    id: UUID
    variant_id: UUID
    product_id: UUID
    product_name: str
    price: Decimal
    variant_attributes: Optional[dict] = None
    product_image: Optional[str] = None
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WishlistResponse(BaseModel):
    id: Optional[UUID] = None
    items: List[WishlistItemResponse] = []
    total_items: int = 0

    model_config = ConfigDict(from_attributes=True)