
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Tuple, Sequence
from alembic.environment import Optional
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.infrastructure.database.models import OrderStatus, Review, Review, ReviewReply, ReviewReply, ReviewReport
from app.api.v1.schemas.review import ReviewCreate, ReviewUpdate, ReviewVoteCreate, ReviewReportCreate, ReviewReplyCreate

class ReviewService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ============================
    # Customer: Create Review
    # ============================
    async def create_review(
        self,
        user_id: UUID,
        data: ReviewCreate,
        image_urls: Optional[List[str]] = None
    ) -> Review:
        # 1. Verify order exists and is delivered
        order = await self.uow.orders.get(data.order_id)
        if not order or order.user_id != user_id:
            raise BusinessError("Order not found")
        if order.order_status != OrderStatus.DELIVERED:
            raise BusinessError("You can only review products from delivered orders")

        # 2. Verify product exists in order
        order_items = await self.uow.order_items.get_by_order(data.order_id)
        if not any(item.product_id == data.product_id for item in order_items):
            raise BusinessError("Product not found in this order")

        # 3. Check if already reviewed (one per order item)
        existing = await self.uow.reviews.get_by_user_and_order(
            user_id, data.order_id, data.product_id
        )
        if existing:
            raise BusinessError("You have already reviewed this product")

        # 4. Create review
        review = await self.uow.reviews.create(
            product_id=data.product_id,
            user_id=user_id,
            order_id=data.order_id,
            rating=data.rating,
            comment=data.comment,
            is_verified=True,   # because it's from a delivered order
            is_hidden=False,
            likes=0,
            dislikes=0
        )

        # 5. Save images
        if image_urls:
            for idx, url in enumerate(image_urls):
                await self.uow.review_images.create(
                    review_id=review.id,
                    url=url,
                    sort_order=idx
                )

        # 6. Update product statistics (async – we'll do it synchronously for simplicity)
        await self._update_product_statistics(data.product_id)

        await self.uow.commit()
        await self.uow.refresh(review)
        return review

    # ============================
    # Customer: Update Review
    # ============================
    async def update_review(
        self,
        user_id: UUID,
        review_id: UUID,
        data: ReviewUpdate,
        image_urls: Optional[List[str]] = None
    ) -> Review:
        review = await self.uow.reviews.get(review_id)
        if not review or review.user_id != user_id:
            raise BusinessError("Review not found")
        if review.deleted_at:
            raise BusinessError("Review has been deleted")

        # Update fields
        if data.rating is not None:
            review.rating = data.rating
        if data.comment is not None:
            review.comment = data.comment
        review.edited_at = datetime.now(timezone.utc)

        # Update images (replace all)
        if image_urls is not None:
            await self.uow.review_images.delete_by_review(review_id)
            for idx, url in enumerate(image_urls):
                await self.uow.review_images.create(
                    review_id=review_id,
                    url=url,
                    sort_order=idx
                )

        # Recalculate product statistics
        await self._update_product_statistics(review.product_id)

        await self.uow.commit()
        await self.uow.refresh(review)
        return review

    # ============================
    # Customer: Delete Review
    # ============================
    async def delete_review(self, user_id: UUID, review_id: UUID) -> None:
        review = await self.uow.reviews.get(review_id)
        if not review or review.user_id != user_id:
            raise BusinessError("Review not found")
        # Soft delete
        review.deleted_at = datetime.now(timezone.utc)
        await self._update_product_statistics(review.product_id)
        await self.uow.commit()

    # ============================
    # Customer: Vote on Review
    # ============================
    async def vote_review(
        self,
        user_id: UUID,
        review_id: UUID,
        data: ReviewVoteCreate
    ) -> dict:
        review = await self.uow.reviews.get(review_id)
        if not review or review.deleted_at:
            raise BusinessError("Review not found")

        # Check if user already voted
        existing = await self.uow.review_votes.get_by_user_and_review(user_id, review_id)
        if existing:
            if existing.vote_type == data.vote_type:
                # Remove vote (toggle off)
                await self.uow.review_votes.delete(existing.id)
                # Update counts
                if data.vote_type == 'like':
                    review.likes -= 1
                else:
                    review.dislikes -= 1
                await self.uow.commit()
                return {"action": "removed", "vote_type": data.vote_type}
            else:
                # Change vote
                existing.vote_type = data.vote_type
                # Update counts: remove old, add new
                if existing.vote_type == 'like':
                    review.dislikes -= 1
                else:
                    review.likes -= 1
                # Now add the new
                if data.vote_type == 'like':
                    review.likes += 1
                else:
                    review.dislikes += 1
                await self.uow.commit()
                await self.uow.refresh(review)
                return {"action": "changed", "vote_type": data.vote_type}
        else:
            # New vote
            await self.uow.review_votes.create(
                review_id=review_id,
                user_id=user_id,
                vote_type=data.vote_type
            )
            if data.vote_type == 'like':
                review.likes += 1
            else:
                review.dislikes += 1
            await self.uow.commit()
            await self.uow.refresh(review)
            return {"action": "added", "vote_type": data.vote_type}

    # ============================
    # Customer: Report Review
    # ============================
    async def report_review(
        self,
        user_id: UUID,
        review_id: UUID,
        data: ReviewReportCreate
    ) -> ReviewReport:
        review = await self.uow.reviews.get(review_id)
        if not review or review.deleted_at:
            raise BusinessError("Review not found")

        existing = await self.uow.review_reports.get_by_user_and_review(user_id, review_id)
        if existing:
            raise BusinessError("You already reported this review")

        report = await self.uow.review_reports.create(
            review_id=review_id,
            user_id=user_id,
            reason=data.reason,
            description=data.description,
            resolved=False
        )
        await self.uow.commit()
        await self.uow.refresh(report)
        return report

    # ============================
    # Seller: Reply to Review
    # ============================
    async def reply_to_review(
        self,
        seller_id: UUID,
        review_id: UUID,
        data: ReviewReplyCreate
    ) -> ReviewReply:
        review = await self.uow.reviews.get(review_id)
        if not review or review.deleted_at:
            raise BusinessError("Review not found")

        # Ensure the seller owns the product
        product = await self.uow.products.get(review.product_id)
        if not product or product.seller_id != seller_id:
            raise BusinessError("You are not authorized to reply to this review")

        # Check if reply exists
        existing = await self.uow.review_replies.get_by_review(review_id)
        if existing:
            existing.reply = data.reply
            existing.updated_at = datetime.now(timezone.utc)
            await self.uow.commit()
            await self.uow.refresh(existing)
            return existing
        else:
            reply = await self.uow.review_replies.create(
                review_id=review_id,
                seller_id=seller_id,
                reply=data.reply
            )
            await self.uow.commit()
            await self.uow.refresh(reply)
            return reply

    # ============================
    # Admin: Hide/Unhide Review
    # ============================
    async def toggle_hide_review(self, review_id: UUID) -> Review:
        review = await self.uow.reviews.toggle_hide(review_id)
        if not review:
            raise BusinessError("Review not found")
        await self._update_product_statistics(review.product_id)
        return review

    # ============================
    # Admin: Delete Review (Hard)
    # ============================
    async def hard_delete_review(self, review_id: UUID) -> None:
        review = await self.uow.reviews.get(review_id)
        if not review:
            raise BusinessError("Review not found")
        # Hard delete
        await self.uow.reviews.delete(review_id)
        await self._update_product_statistics(review.product_id)
        await self.uow.commit()

    # ============================
    # Public: Get Product Reviews
    # ============================
    async def get_product_reviews(
        self,
        product_id: UUID,
        skip: int,
        limit: int,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> dict:
        reviews, total = await self.uow.reviews.get_by_product(
            product_id,
            skip,
            limit,
            include_hidden=False,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return {
            "data": reviews,
            "total": total,
            "page": skip // limit + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }

    # ============================
    # Public: Get Review Details
    # ============================
    async def get_review(self, review_id: UUID) -> Review:
        review = await self.uow.reviews.get_with_details(review_id)
        if not review or review.deleted_at or review.is_hidden:
            raise BusinessError("Review not found")
        return review

    # ============================
    # Public: Get Review Statistics
    # ============================
    async def get_review_statistics(self, product_id: UUID) -> dict:
        stats = await self.uow.reviews.get_statistics(product_id)
        return stats

    # ============================
    # Admin: List All Reviews (with filters)
    # ============================
    async def admin_list_reviews(
        self,
        skip: int,
        limit: int,
        product_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        is_hidden: Optional[bool] = None,
        include_deleted: bool = False,
        ) -> Tuple[Sequence[Review], int]:
        """Admin list with filters."""
        return await self.uow.reviews.admin_list(
            skip=skip,
            limit=limit,
            product_id=product_id,
            user_id=user_id,
            is_hidden=is_hidden,
            include_deleted=include_deleted,
        )

    # ============================
    # Admin: List Pending Reports
    # ============================
    async def get_pending_reports(self, skip: int, limit: int) -> Sequence[ReviewReport]:
        return await self.uow.review_reports.get_pending(skip, limit)

    # ============================
    # Admin: Resolve Report
    # ============================
    async def resolve_report(self, report_id: UUID) -> ReviewReport:
        report = await self.uow.review_reports.get(report_id)
        if not report:
            raise BusinessError("Report not found")
        report.resolved = True
        await self.uow.commit()
        await self.uow.refresh(report)
        return report

    # ============================
    # Helper: Update Product Statistics
    # ============================
    async def _update_product_statistics(self, product_id: UUID) -> None:
        stats = await self.uow.reviews.get_statistics(product_id)
        product_stat = await self.uow.product_statistics.get_by_product(product_id)
        if product_stat:
            product_stat.average_rating = stats["average_rating"]
            product_stat.total_reviews = stats["total_reviews"]
        await self.uow.commit()