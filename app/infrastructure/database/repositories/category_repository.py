from typing import Any, Dict, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import func, select

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
    
    async def get_admin(self, id: UUID, include_deleted: bool = False) -> Optional[Category]:
        """
        Get a category by ID (admin version).
        If include_deleted is True, returns soft-deleted categories as well.
        """
        stmt = select(Category).filter(Category.id == id)
        if not include_deleted:
            stmt = stmt.filter(Category.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_admin(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Sequence[Category], int]:
        """
        Admin: get categories with filters and pagination, optionally including soft-deleted.
        Returns a tuple (items, total_count).
        """
        if filters is None:
            filters = {}

        # Build main query
        stmt = select(Category)

        # Filter soft-deleted
        if not filters.get("include_deleted", False):
            stmt = stmt.filter(Category.deleted_at.is_(None))

        # Apply other filters
        if filters.get("name"):
            stmt = stmt.filter(Category.name.ilike(f"%{filters['name']}%"))
        if filters.get("slug"):
            stmt = stmt.filter(Category.slug.ilike(f"%{filters['slug']}%"))
        if filters.get("parent_id") is not None:
            stmt = stmt.filter(Category.parent_id == filters["parent_id"])
        if filters.get("is_active") is not None:
            stmt = stmt.filter(Category.is_active == filters["is_active"])

        # Count total
        count_stmt = select(func.count()).select_from(Category)
        # Apply the same filters to the count query
        if not filters.get("include_deleted", False):
            count_stmt = count_stmt.filter(Category.deleted_at.is_(None))
        if filters.get("name"):
            count_stmt = count_stmt.filter(Category.name.ilike(f"%{filters['name']}%"))
        if filters.get("slug"):
            count_stmt = count_stmt.filter(Category.slug.ilike(f"%{filters['slug']}%"))
        if filters.get("parent_id") is not None:
            count_stmt = count_stmt.filter(Category.parent_id == filters["parent_id"])
        if filters.get("is_active") is not None:
            count_stmt = count_stmt.filter(Category.is_active == filters["is_active"])

        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Order and paginate
        stmt = stmt.order_by(Category.name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all(), total