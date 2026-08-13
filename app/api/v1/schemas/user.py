from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.infrastructure.database.models import UserRole
from app.core.config import settings

# ----- Base schemas -----

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    phone: str
    password: str = Field(..., min_length=8, max_length=72)
    profile_image: Optional[str] = None


class LoginRequest(BaseModel):
    login: str  # email or phone
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ----- Public Profile -----

class PublicUserProfileResponse(BaseModel):
    id: UUID
    full_name: str
    profile_image: Optional[str]
    role: UserRole
    
    # Seller fields (optional, only if user is a seller)
    shop_name: Optional[str] = None
    shop_slug: Optional[str] = None
    logo: Optional[str] = None
    cover_image: Optional[str] = None
    shop_description: Optional[str] = None
    average_rating: Optional[float] = None
    total_products: Optional[int] = None
    total_orders: Optional[int] = None
    joined_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ----- OTP Schemas -----

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=settings.OTP_LENGTH, max_length=settings.OTP_LENGTH)


class OTPResendRequest(BaseModel):
    email: EmailStr


# ----- Nested Shop Profile (for Seller) -----

class ShopProfile(BaseModel):
    id: UUID
    name: str = Field(..., alias="shop_name")
    slug: str = Field(..., alias="shop_slug")
    logo: Optional[str]
    banner: Optional[str] = Field(None, alias="cover_image")
    description: Optional[str] = Field(None, alias="shop_description")
    rating: Optional[float] = Field(None, alias="average_rating")
    total_products: int = 0
    total_followers: int = 0
    verification_status: str = "verified"
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ----- Nested Admin Profile -----

class AdminProfile(BaseModel):
    permissions: List[str] = [
        "users.read",
        "users.write",
        "products.manage",
        "orders.manage",
        "reviews.manage",
        "shops.manage"
    ]
    last_login: Optional[datetime]
    super_admin: bool = True

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ----- Authenticated Profile Response -----

class AuthenticatedUserProfileResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str
    profile_image: Optional[str]
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Role‑specific nested objects (only one will be set)
    shop: Optional[ShopProfile] = None
    admin: Optional[AdminProfile] = None

    model_config = ConfigDict(from_attributes=True)
    
class RegistrationOTPRequest(UserCreate):
    """Same as UserCreate, but used for requesting OTP."""
    pass

class RegistrationOTPResponse(BaseModel):
    message: str
    email: str
    expires_in: int

class UserRegisterWithOTP(UserCreate):
    otp: str = Field(..., min_length=6, max_length=6)