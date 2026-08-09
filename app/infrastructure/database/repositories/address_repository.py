from sqlalchemy import select, update, func
from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.models import Address
from .base import AsyncBaseRepository

class AddressRepository(AsyncBaseRepository[Address]):
    async def get(self, id: UUID) -> Optional[Address]:
        result = await self.session.execute(
            select(Address).filter(Address.id == id, Address.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Address]:
        result = await self.session.execute(
            select(Address).filter(Address.deleted_at.is_(None)).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_user(self, user_id: UUID) -> Sequence[Address]:
        result = await self.session.execute(
            select(Address).filter(Address.user_id == user_id, Address.deleted_at.is_(None))
        )
        return result.scalars().all()

    async def get_default(self, user_id: UUID) -> Optional[Address]:
        result = await self.session.execute(
            select(Address).filter(
                Address.user_id == user_id,
                Address.is_default == True,
                Address.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: UUID) -> int:
        """Count active addresses for a user."""
        result = await self.session.execute(
            select(func.count()).filter(
                Address.user_id == user_id,
                Address.deleted_at.is_(None)
            )
        )
        return result.scalar() or 0

    async def set_default(self, address_id: Optional[UUID], user_id: UUID) -> Optional[Address]:
        """Set a specific address as default, or clear all defaults if address_id is None."""
        # Clear default for all user's addresses
        await self.session.execute(
            update(Address)
            .where(Address.user_id == user_id, Address.deleted_at.is_(None))
            .values(is_default=False)
        )
        if address_id is None:
            await self.session.commit()
            return None
        # Set the specified address as default
        stmt = (
            update(Address)
            .where(Address.id == address_id, Address.user_id == user_id, Address.deleted_at.is_(None))
            .values(is_default=True)
            .returning(Address)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()