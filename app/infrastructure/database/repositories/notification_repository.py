from sqlalchemy import select, update, func
from uuid import UUID
from datetime import datetime
from typing import Sequence, Optional
from app.infrastructure.database.models import Notification, NotificationType
from .base import AsyncBaseRepository

class NotificationRepository(AsyncBaseRepository[Notification]):
    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        is_read: Optional[bool] = None
    ) -> Sequence[Notification]:
        stmt = select(Notification).filter(Notification.user_id == user_id)
        if is_read is not None:
            stmt = stmt.filter(Notification.is_read == is_read)
        stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True)
            .returning(Notification)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_all_as_read(self, user_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def count_unread(self, user_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        return result.scalar() or 0

    async def delete_by_user(self, user_id: UUID) -> int:
        # For deleting all notifications of a user (hard delete)
        stmt = select(Notification).filter(Notification.user_id == user_id)
        result = await self.session.execute(stmt)
        notifications = result.scalars().all()
        for n in notifications:
            await self.session.delete(n)
        return len(notifications)