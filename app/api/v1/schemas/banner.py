from pydantic import BaseModel, ConfigDict, Field, UUID4
from datetime import datetime
from typing import Optional
from uuid import UUID

class BannerBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    image_url: str = Field(..., max_length=500)
    link_url: Optional[str] = Field(None, max_length=500)
    product_id: Optional[UUID4] = None
    category_id: Optional[UUID4] = None
    position: int = 0
    is_active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class BannerCreate(BannerBase):
    pass

class BannerUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    link_url: Optional[str] = Field(None, max_length=500)
    product_id: Optional[UUID4] = None
    category_id: Optional[UUID4] = None
    position: Optional[int] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class BannerResponse(BannerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)