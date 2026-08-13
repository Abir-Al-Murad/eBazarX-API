from sqlalchemy import select, func, update
from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.models import Seller, SellerStatus
from .base import AsyncBaseRepository

class SellerRepository(AsyncBaseRepository[Seller]):
    async def get(self, id: UUID) -> Optional[Seller]:
        result = await self.session.execute(
            select(Seller).filter(Seller.id == id, Seller.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Optional[Seller]:
        result = await self.session.execute(
            select(Seller).filter(Seller.user_id == user_id, Seller.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Seller]:
        result = await self.session.execute(
            select(Seller).filter(Seller.shop_slug == slug, Seller.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, seller_id: UUID) -> Optional[Seller]:
        """Alias for get() – kept for clarity when used in service."""
        return await self.get(seller_id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[SellerStatus] = None,
    ) -> Sequence[Seller]:
        stmt = select(Seller).filter(Seller.deleted_at.is_(None))
        if status is not None:
            stmt = stmt.filter(Seller.status == status)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_status(self, status: SellerStatus, skip: int = 0, limit: int = 100) -> Sequence[Seller]:
        result = await self.session.execute(
            select(Seller)
            .filter(Seller.status == status, Seller.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_all(self) -> int:
        result = await self.session.execute(
            select(func.count()).filter(Seller.deleted_at.is_(None))
        )
        return result.scalar() or 0

    async def count_by_status(self, status: SellerStatus) -> int:
        result = await self.session.execute(
            select(func.count()).filter(
                Seller.status == status,
                Seller.deleted_at.is_(None)
            )
        )
        return result.scalar() or 0

    async def update_status(self, seller_id: UUID, status: SellerStatus) -> Optional[Seller]:
        seller = await self.get(seller_id)
        if seller:
            seller.status = status
            await self.session.commit()
            await self.session.refresh(seller)
        return seller


    async def update(self, id: UUID, **kwargs) -> Optional[Seller]:
        stmt = update(Seller).where(Seller.id == id).values(**kwargs).returning(Seller)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()