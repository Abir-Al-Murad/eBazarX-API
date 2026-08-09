from celery import result
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import User
from app.infrastructure.database.repositories.base import AsyncBaseRepository
from typing import Optional
from uuid import UUID

class UserRepository(AsyncBaseRepository[User]):
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Optional[User]:
        result = await self.session.execute(select(User).filter(User.phone == phone))
        return result.scalar_one_or_none()
    
    async def count_active(self) -> int:
        result = await self.session.execute(
        select(func.count()).filter(User.is_active == True, User.deleted_at.is_(None))
    )
        return result.scalar() or 0
    async def get_with_seller(self, user_id: UUID) -> Optional[User]:
        """Fetch user with seller relationship eager loaded."""
        stmt = (
            select(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .options(selectinload(User.seller))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_public_profile(self, user_id: UUID) -> Optional[User]:
        """Fetch user with seller for public profile (no sensitive fields)."""
        stmt = (
            select(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .options(selectinload(User.seller))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()