from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.infrastructure.database.models import SellerStatus

# ============================
# Seller Application
# ============================
class SellerApplicationCreate(BaseModel):
    shop_name: str = Field(..., max_length=255)
    shop_slug: str = Field(..., max_length=255, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    description: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    country: str = "Bangladesh"
    trade_license: Optional[str] = None
    nid: Optional[str] = None
    tin: Optional[str] = None

class SellerApplicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    shop_name: str
    shop_slug: str
    status: SellerStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================
# Admin Status Update
# ============================
class SellerStatusUpdate(BaseModel):
    status: SellerStatus
    admin_notes: Optional[str] = None

class SellerAdminListResponse(BaseModel):
    id: UUID
    user_id: UUID
    shop_name: str
    shop_slug: str
    status: SellerStatus
    created_at: datetime
    updated_at: datetime
    user_email: Optional[str] = None
    user_phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)