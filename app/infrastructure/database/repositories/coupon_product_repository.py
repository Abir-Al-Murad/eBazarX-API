from sqlalchemy import delete, select
from uuid import UUID
from typing import Sequence
from app.infrastructure.database.models import CouponProduct
from .base import AsyncBaseRepository

class CouponProductRepository(AsyncBaseRepository[CouponProduct]):
    async def delete_by_coupon(self, coupon_id: UUID) -> None:
        stmt = delete(CouponProduct).where(CouponProduct.coupon_id == coupon_id)
        await self.session.execute(stmt)

    async def get_by_coupon(self, coupon_id: UUID) -> Sequence[CouponProduct]:
        result = await self.session.execute(
            select(CouponProduct).filter(CouponProduct.coupon_id == coupon_id)
        )
        return result.scalars().all()