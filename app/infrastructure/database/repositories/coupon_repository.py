from uuid import UUID

from sqlalchemy import select, and_, func
from datetime import datetime
from typing import Optional, Sequence
from app.infrastructure.database.models import Coupon, CouponUsage, CouponProduct, CouponCategory
from app.infrastructure.database.repositories.base import AsyncBaseRepository

class CouponRepository(AsyncBaseRepository[Coupon]):
    async def get_by_code(self, code: str) -> Optional[Coupon]:
        result = await self.session.execute(
            select(Coupon).filter(Coupon.code == code)
        )
        return result.scalar_one_or_none()

    async def get_active_coupons(self, current_time: datetime, seller_id: Optional[UUID] = None) -> Sequence[Coupon]:
        stmt = select(Coupon).filter(
            Coupon.is_active == True,
            Coupon.start_date <= current_time,
            Coupon.end_date >= current_time
        )
        if seller_id is not None:
            stmt = stmt.filter(Coupon.seller_id == seller_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_seller(self, seller_id: UUID, skip: int = 0, limit: int = 100) -> Sequence[Coupon]:
        result = await self.session.execute(
            select(Coupon).filter(Coupon.seller_id == seller_id).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_usage_count(self, coupon_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).filter(CouponUsage.coupon_id == coupon_id)
        )
        return result.scalar() or 0

    async def get_user_usage_count(self, coupon_id: UUID, user_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).filter(CouponUsage.coupon_id == coupon_id, CouponUsage.user_id == user_id)
        )
        return result.scalar() or 0

    async def get_coupon_products(self, coupon_id: UUID) -> Sequence[CouponProduct]:
        result = await self.session.execute(
            select(CouponProduct).filter(CouponProduct.coupon_id == coupon_id)
        )
        return result.scalars().all()

    async def get_coupon_categories(self, coupon_id: UUID) -> Sequence[CouponCategory]:
        result = await self.session.execute(
            select(CouponCategory).filter(CouponCategory.coupon_id == coupon_id)
        )
        return result.scalars().all()