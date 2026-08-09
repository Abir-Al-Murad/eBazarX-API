from sqlalchemy import delete, select
from uuid import UUID
from typing import Sequence
from app.infrastructure.database.models import CouponCategory
from .base import AsyncBaseRepository

class CouponCategoryRepository(AsyncBaseRepository[CouponCategory]):
    async def delete_by_coupon(self, coupon_id: UUID) -> None:
        stmt = delete(CouponCategory).where(CouponCategory.coupon_id == coupon_id)
        await self.session.execute(stmt)

    async def get_by_coupon(self, coupon_id: UUID) -> Sequence[CouponCategory]:
        result = await self.session.execute(
            select(CouponCategory).filter(CouponCategory.coupon_id == coupon_id)
        )
        return result.scalars().all()