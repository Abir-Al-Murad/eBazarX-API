from pydantic import BaseModel, ConfigDict, Field, UUID4
from uuid import UUID
from datetime import datetime
from typing import Optional

class AddressBase(BaseModel):
    full_name: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=20)
    division: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    upazila: Optional[str] = Field(None, max_length=100)
    area: Optional[str] = Field(None, max_length=255)
    address_line: str = Field(..., max_length=500)
    postal_code: Optional[str] = Field(None, max_length=20)
    label: str = Field("Home", max_length=50)
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    division: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    upazila: Optional[str] = Field(None, max_length=100)
    area: Optional[str] = Field(None, max_length=255)
    address_line: Optional[str] = Field(None, max_length=500)
    postal_code: Optional[str] = Field(None, max_length=20)
    label: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = None

class AddressResponse(AddressBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)