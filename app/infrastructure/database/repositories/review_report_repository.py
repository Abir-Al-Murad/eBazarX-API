from sqlalchemy import select, func
from uuid import UUID
from typing import Sequence, Optional
from app.infrastructure.database.models import ReviewReport
from .base import AsyncBaseRepository

class ReviewReportRepository(AsyncBaseRepository[ReviewReport]):
    async def get_by_review(self, review_id: UUID) -> Sequence[ReviewReport]:
        result = await self.session.execute(
            select(ReviewReport).filter(ReviewReport.review_id == review_id)
        )
        return result.scalars().all()

    async def get_by_user_and_review(self, user_id: UUID, review_id: UUID) -> Optional[ReviewReport]:
        result = await self.session.execute(
            select(ReviewReport).filter(
                ReviewReport.user_id == user_id,
                ReviewReport.review_id == review_id
            )
        )
        return result.scalar_one_or_none()

    async def get_pending(self, skip: int = 0, limit: int = 20) -> Sequence[ReviewReport]:
        result = await self.session.execute(
            select(ReviewReport).filter(ReviewReport.resolved == False)
            .offset(skip).limit(limit)
            .order_by(ReviewReport.created_at.desc())
        )
        return result.scalars().all()