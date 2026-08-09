from sqlalchemy import select
from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.models import ReviewReply
from .base import AsyncBaseRepository

class ReviewReplyRepository(AsyncBaseRepository[ReviewReply]):
    async def get_by_review(self, review_id: UUID) -> Optional[ReviewReply]:
        result = await self.session.execute(
            select(ReviewReply).filter(ReviewReply.review_id == review_id)
        )
        return result.scalar_one_or_none()

    async def get_by_seller(self, seller_id: UUID, skip: int = 0, limit: int = 20) -> Sequence[ReviewReply]:
        result = await self.session.execute(
            select(ReviewReply).filter(ReviewReply.seller_id == seller_id)
            .offset(skip).limit(limit)
            .order_by(ReviewReply.created_at.desc())
        )
        return result.scalars().all()