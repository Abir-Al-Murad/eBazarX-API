from sqlalchemy import select, func
from uuid import UUID
from typing import Optional
from app.infrastructure.database.models import ReviewVote
from .base import AsyncBaseRepository

class ReviewVoteRepository(AsyncBaseRepository[ReviewVote]):
    async def get_by_user_and_review(self, user_id: UUID, review_id: UUID) -> Optional[ReviewVote]:
        result = await self.session.execute(
            select(ReviewVote).filter(
                ReviewVote.user_id == user_id,
                ReviewVote.review_id == review_id
            )
        )
        return result.scalar_one_or_none()

    async def count_likes(self, review_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).filter(
                ReviewVote.review_id == review_id,
                ReviewVote.vote_type == 'like'
            )
        )
        return result.scalar() or 0

    async def count_dislikes(self, review_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).filter(
                ReviewVote.review_id == review_id,
                ReviewVote.vote_type == 'dislike'
            )
        )
        return result.scalar() or 0