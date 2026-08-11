from ast import stmt

from sqlalchemy import select, func, and_, or_, desc, asc
from uuid import UUID
from typing import Optional, Sequence, Dict, List, Tuple
from datetime import datetime, timezone

from sqlalchemy.orm import selectinload
from app.infrastructure.database.models import Review, ReviewImage, ReviewVote, ReviewReport, ReviewReply
from .base import AsyncBaseRepository
from sqlalchemy import desc, asc, func

class ReviewRepository(AsyncBaseRepository[Review]):
    async def get(self, id: UUID) -> Optional[Review]:
        result = await self.session.execute(
            select(Review).filter(Review.id == id, Review.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_with_details(self, id: UUID) -> Optional[Review]:
        result = await self.session.execute(
            select(Review)
            .filter(Review.id == id, Review.deleted_at.is_(None))
            .options(
                selectinload(Review.images),
                selectinload(Review.reply).selectinload(ReviewReply.seller),
                selectinload(Review.user)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_product(
        self,
        product_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_hidden: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[Sequence[Review], int]:
        stmt = select(Review).filter(
            Review.product_id == product_id,
            Review.deleted_at.is_(None)
        )
        if not include_hidden:
            stmt = stmt.filter(Review.is_hidden == False)

        # Sorting
        if sort_by == "created_at":
            order = desc(Review.created_at) if sort_order == "desc" else asc(Review.created_at)
        elif sort_by == "rating":
            order = desc(Review.rating) if sort_order == "desc" else asc(Review.rating)
        elif sort_by == "likes":
            order = desc(Review.likes) if sort_order == "desc" else asc(Review.likes)
        else:
            order = desc(Review.created_at)
        stmt = stmt.order_by(order).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        items = result.scalars().all()

        # Count total
        count_stmt = select(func.count()).filter(
            Review.product_id == product_id,
            Review.deleted_at.is_(None)
        )
        if not include_hidden:
            count_stmt = count_stmt.filter(Review.is_hidden == False)
        total = (await self.session.execute(count_stmt)).scalar() or 0

        return items, total

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[Sequence[Review], int]:
        stmt = select(Review).filter(
            Review.user_id == user_id,
            Review.deleted_at.is_(None)
        ).order_by(desc(Review.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()

        count_stmt = select(func.count()).filter(
            Review.user_id == user_id,
            Review.deleted_at.is_(None)
        )
        total = (await self.session.execute(count_stmt)).scalar() or 0
        return items, total


    async def get_by_user_and_product(self, user_id: UUID, product_id: UUID) -> Optional[Review]:
        stmt = select(Review).filter(
            Review.user_id == user_id,
            Review.product_id == product_id,
            Review.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()



    async def get_by_user_and_order(
        self,
        user_id: UUID,
        order_id: UUID,
        product_id: UUID
    ) -> Optional[Review]:
        result = await self.session.execute(
            select(Review).filter(
                Review.user_id == user_id,
                Review.order_id == order_id,
                Review.product_id == product_id,
                Review.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()




    async def admin_list(
        self,
        skip: int = 0,
        limit: int = 20,
        product_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        is_hidden: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> Tuple[Sequence[Review], int]:
        """Admin list with filters, including soft-deleted if requested."""
        stmt = select(Review)
        if not include_deleted:
            stmt = stmt.filter(Review.deleted_at.is_(None))
        if product_id:
            stmt = stmt.filter(Review.product_id == product_id)
        if user_id:
            stmt = stmt.filter(Review.user_id == user_id)
        if is_hidden is not None:
            stmt = stmt.filter(Review.is_hidden == is_hidden)
        stmt = stmt.order_by(desc(Review.created_at)).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        items = result.scalars().all()

    # Count total
        count_stmt = select(func.count()).select_from(Review)
        if not include_deleted:
            count_stmt = count_stmt.filter(Review.deleted_at.is_(None))
        if product_id:
            count_stmt = count_stmt.filter(Review.product_id == product_id)
        if user_id:
            count_stmt = count_stmt.filter(Review.user_id == user_id)
        if is_hidden is not None:
            count_stmt = count_stmt.filter(Review.is_hidden == is_hidden)

        total = (await self.session.execute(count_stmt)).scalar() or 0
        return items, total

    async def get_statistics(self, product_id: UUID) -> Dict:
        # Average rating
        avg_stmt = select(func.avg(Review.rating)).filter(
            Review.product_id == product_id,
            Review.is_hidden == False,
            Review.deleted_at.is_(None)
        )
        avg = (await self.session.execute(avg_stmt)).scalar() or 0.0

        # Total count
        total_stmt = select(func.count()).filter(
            Review.product_id == product_id,
            Review.is_hidden == False,
            Review.deleted_at.is_(None)
        )
        total = (await self.session.execute(total_stmt)).scalar() or 0

        # Rating distribution
        dist_stmt = select(
            Review.rating,
            func.count()
        ).filter(
            Review.product_id == product_id,
            Review.is_hidden == False,
            Review.deleted_at.is_(None)
        ).group_by(Review.rating)
        dist_result = await self.session.execute(dist_stmt)
        dist = {r: 0 for r in range(1, 6)}
        for rating, count in dist_result:
            dist[rating] = count

        return {
            "average_rating": round(avg, 2) if avg else 0.0,
            "total_reviews": total,
            "rating_distribution": dist
        }

    async def soft_delete(self, id: UUID) -> Optional[Review]:
        review = await self.get(id)
        if review:
            review.deleted_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(review)
        return review

    async def toggle_hide(self, id: UUID) -> Optional[Review]:
        review = await self.get(id)
        if review:
            review.is_hidden = not review.is_hidden
            await self.session.commit()
            await self.session.refresh(review)
        return review