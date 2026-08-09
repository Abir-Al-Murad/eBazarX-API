from sqlalchemy import select, delete
from uuid import UUID
from typing import Sequence, Optional
from app.infrastructure.database.models import ReviewImage
from .base import AsyncBaseRepository

class ReviewImageRepository(AsyncBaseRepository[ReviewImage]):
    async def get_by_review(self, review_id: UUID) -> Sequence[ReviewImage]:
        result = await self.session.execute(
            select(ReviewImage).filter(ReviewImage.review_id == review_id).order_by(ReviewImage.sort_order)
        )
        return result.scalars().all()

    async def delete_by_review(self, review_id: UUID) -> int:
        stmt = delete(ReviewImage).where(ReviewImage.review_id == review_id)
        result = await self.session.execute(stmt)
        return result.rowcount