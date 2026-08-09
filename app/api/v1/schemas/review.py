from pydantic import BaseModel, ConfigDict, Field, UUID4, validator
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

# ============================
# Review Image
# ============================
class ReviewImageBase(BaseModel):
    url: str
    sort_order: int = 0

class ReviewImageCreate(ReviewImageBase):
    pass

class ReviewImageResponse(ReviewImageBase):
    id: UUID
    review_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================
# Review Vote
# ============================
class ReviewVoteCreate(BaseModel):
    vote_type: str  # 'like' or 'dislike'

    @validator('vote_type')
    def validate_vote_type(cls, v):
        if v not in ('like', 'dislike'):
            raise ValueError('vote_type must be "like" or "dislike"')
        return v

class ReviewVoteResponse(BaseModel):
    review_id: UUID
    vote_type: str

    model_config = ConfigDict(from_attributes=True)

# ============================
# Review Report
# ============================
class ReviewReportCreate(BaseModel):
    reason: str
    description: Optional[str] = None

class ReviewReportResponse(BaseModel):
    id: UUID
    review_id: UUID
    user_id: UUID
    reason: str
    description: Optional[str]
    resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================
# Review Reply
# ============================
class ReviewReplyCreate(BaseModel):
    reply: str

class ReviewReplyResponse(BaseModel):
    id: UUID
    review_id: UUID
    seller_id: UUID
    reply: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================
# Review
# ============================
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    images: Optional[List[str]] = None  # URLs for creating

class ReviewCreate(ReviewBase):
    order_id: UUID4
    product_id: UUID4

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    images: Optional[List[str]] = None

class ReviewResponse(BaseModel):
    id: UUID
    product_id: UUID
    user_id: UUID
    order_id: Optional[UUID]
    rating: int
    comment: Optional[str]
    is_verified: bool
    likes: int
    dislikes: int
    is_hidden: bool
    edited_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    images: List[ReviewImageResponse] = []
    reply: Optional[ReviewReplyResponse] = None
    user_full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ReviewStatisticsResponse(BaseModel):
    average_rating: Decimal
    total_reviews: int
    rating_distribution: dict  # {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

class ReviewListResponse(BaseModel):
    data: List[ReviewResponse]
    total: int
    page: int
    size: int
    pages: int