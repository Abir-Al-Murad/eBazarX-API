from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select

from app.infrastructure.database.models import Category
from .base import AsyncBaseRepository


class CategoryRepository(AsyncBaseRepository[Category]):

    async def get(self, id: UUID) -> Optional[Category]:
        """Get category by id."""
        result = await self.session.execute(
            select(Category).where(
                Category.id == id,
                Category.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Category]:
        """Get all active categories."""
        result = await self.session.execute(
            select(Category)
            .where(Category.deleted_at.is_(None))
            .order_by(Category.name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_root_categories(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Category]:
        """Get only parent categories."""
        result = await self.session.execute(
            select(Category)
            .where(
                Category.parent_id.is_(None),
                Category.deleted_at.is_(None),
                Category.is_active.is_(True),
            )
            .order_by(Category.name)
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all()

    async def get_children(
        self,
        parent_id: UUID,
    ) -> Sequence[Category]:
        """Get direct children of a category."""
        result = await self.session.execute(
            select(Category)
            .where(
                Category.parent_id == parent_id,
                Category.deleted_at.is_(None),
                Category.is_active.is_(True),
            )
            .order_by(Category.name)
        )

        return result.scalars().all()

    async def has_children(self, parent_id: UUID) -> bool:
        """Check whether category has children."""
        result = await self.session.execute(
            select(Category.id)
            .where(
                Category.parent_id == parent_id,
                Category.deleted_at.is_(None),
                Category.is_active.is_(True),
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def get_by_slug(
        self,
        slug: str,
    ) -> Optional[Category]:
        """Get category by slug."""
        result = await self.session.execute(
            select(Category).where(
                Category.slug == slug,
                Category.deleted_at.is_(None),
            )
        )

        return result.scalar_one_or_none()

    async def get_parent(
        self,
        parent_id: UUID,
    ) -> Optional[Category]:
        """Get parent category."""
        return await self.get(parent_id)

    async def check_slug_exists(
        self,
        slug: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if slug already exists."""

        stmt = select(Category.id).where(
            Category.slug == slug,
            Category.deleted_at.is_(None),
        )

        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None