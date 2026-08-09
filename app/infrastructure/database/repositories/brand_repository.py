from sqlalchemy import select
from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.models import Brand
from .base import AsyncBaseRepository

class BrandRepository(AsyncBaseRepository[Brand]):
    async def get(self, id: UUID) -> Optional[Brand]:
        result = await self.session.execute(
            select(Brand).filter(Brand.id == id, Brand.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Brand]:
        result = await self.session.execute(
            select(Brand)
            .filter(Brand.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_slug(self, slug: str) -> Optional[Brand]:
        result = await self.session.execute(
            select(Brand).filter(Brand.slug == slug, Brand.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def check_slug_exists(self, slug: str, exclude_id: Optional[UUID] = None) -> bool:
        stmt = select(Brand).filter(Brand.slug == slug, Brand.deleted_at.is_(None))
        if exclude_id:
            stmt = stmt.filter(Brand.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None