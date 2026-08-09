from pydantic import BaseModel, ConfigDict, Field, UUID4
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from app.infrastructure.database.models import DiscountType

# ----- Coupon Base -----
class CouponBase(BaseModel):
    code: str = Field(..., max_length=50, pattern=r'^[A-Z0-9_]+$')
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: Decimal = Field(..., gt=0)
    min_order_amount: Optional[Decimal] = Field(None, ge=0)
    max_discount: Optional[Decimal] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, gt=0)
    per_user_limit: Optional[int] = Field(None, gt=0)
    is_active: bool = True
    start_date: datetime
    end_date: datetime

class CouponCreate(CouponBase):
    # For admin: seller_id optional; for seller: seller_id will be set automatically
    seller_id: Optional[UUID4] = None
    product_ids: Optional[List[UUID4]] = None
    category_ids: Optional[List[UUID4]] = None

class CouponUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50, pattern=r'^[A-Z0-9_]+$')
    description: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = Field(None, gt=0)
    min_order_amount: Optional[Decimal] = Field(None, ge=0)
    max_discount: Optional[Decimal] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, gt=0)
    per_user_limit: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    product_ids: Optional[List[UUID4]] = None
    category_ids: Optional[List[UUID4]] = None

class CouponResponse(CouponBase):
    id: UUID
    seller_id: Optional[UUID]
    used_count: int = 0  # computed from coupon usage
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----- Coupon Validation -----
class CouponValidationRequest(BaseModel):
    code: str
    subtotal: Decimal
    user_id: UUID4

class CouponValidationResponse(BaseModel):
    valid: bool
    discount_amount: Decimal = Decimal(0)
    message: Optional[str] = None
    coupon_id: Optional[UUID] = None