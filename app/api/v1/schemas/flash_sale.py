from pydantic import BaseModel, ConfigDict, Field, UUID4
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

class FlashSaleProductBase(BaseModel):
    product_id: UUID4
    discount_price: Decimal = Field(..., gt=0)
    stock_limit: int = Field(..., ge=0)

class FlashSaleProductCreate(FlashSaleProductBase):
    pass

class FlashSaleProductResponse(FlashSaleProductBase):
    id: UUID
    sold: int
    flash_sale_id: UUID

    model_config = ConfigDict(from_attributes=True)

class FlashSaleBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    is_active: bool = True

class FlashSaleCreate(FlashSaleBase):
    products: List[FlashSaleProductCreate] = []

class FlashSaleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    products: Optional[List[FlashSaleProductCreate]] = None

class FlashSaleResponse(FlashSaleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    products: List[FlashSaleProductResponse] = []

    model_config = ConfigDict(from_attributes=True)