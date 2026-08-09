from pydantic import BaseModel, ConfigDict, Field, UUID4
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.infrastructure.database.models import ProductApprovalStatus

# ----- Variant -----
class ProductVariantBase(BaseModel):
    sku: str = Field(..., max_length=100)
    price_override: Optional[Decimal] = None
    stock: int = Field(default=0, ge=0)
    attributes: Dict[str, str] = Field(default_factory=dict)

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariantUpdate(BaseModel):
    sku: Optional[str] = Field(None, max_length=100)
    price_override: Optional[Decimal] = None
    stock: Optional[int] = Field(None, ge=0)
    attributes: Optional[Dict[str, str]] = None

class ProductVariantResponse(ProductVariantBase):
    id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----- Image -----
class ProductImageBase(BaseModel):
    url: str = Field(..., max_length=500)
    is_primary: bool = False
    sort_order: int = 0

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageResponse(ProductImageBase):
    id: UUID
    product_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----- Product -----
class ProductBase(BaseModel):
    category_id: UUID4
    brand_id: Optional[UUID4] = None
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    discount_price: Optional[Decimal] = Field(None, ge=0)
    sku: str = Field(..., max_length=100)
    seo_title: Optional[str] = Field(None, max_length=255)
    seo_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, Any]] = None

class ProductCreate(ProductBase):
    variants: List[ProductVariantCreate] = Field(default_factory=list)
    images: List[ProductImageCreate] = Field(default_factory=list)

class ProductUpdate(BaseModel):
    category_id: Optional[UUID4] = None
    brand_id: Optional[UUID4] = None
    name: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=255, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    discount_price: Optional[Decimal] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    seo_title: Optional[str] = Field(None, max_length=255)
    seo_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    tags: Optional[List[str]] = None
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: UUID
    seller_id: UUID
    is_active: bool
    approval_status: ProductApprovalStatus
    average_rating: Decimal = Decimal('0')
    total_reviews: int = 0
    total_sales: int = 0
    created_at: datetime
    updated_at: datetime
    variants: List[ProductVariantResponse] = Field(default_factory=list)
    images: List[ProductImageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class ProductApprovalUpdate(BaseModel):
    approval_status: ProductApprovalStatus
    notes: Optional[str] = None