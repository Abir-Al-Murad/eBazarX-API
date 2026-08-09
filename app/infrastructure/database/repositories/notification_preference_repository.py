from sqlalchemy import select, update
from uuid import UUID
from typing import Optional, Dict
from app.infrastructure.database.models import NotificationPreference
from .base import AsyncBaseRepository

class NotificationPreferenceRepository(AsyncBaseRepository[NotificationPreference]):
    async def get_by_user(self, user_id: UUID) -> Optional[NotificationPreference]:
        result = await self.session.execute(
            select(NotificationPreference).filter(NotificationPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        user_id: UUID,
        push_enabled: bool = True,
        email_enabled: bool = True,
        sms_enabled: bool = False,
        in_app_enabled: bool = True,
        preferences: Optional[Dict] = None
    ) -> NotificationPreference:
        existing = await self.get_by_user(user_id)
        if existing:
            existing.push_enabled = push_enabled
            existing.email_enabled = email_enabled
            existing.sms_enabled = sms_enabled
            existing.in_app_enabled = in_app_enabled
            existing.preferences = preferences
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            pref = await self.create(
                user_id=user_id,
                push_enabled=push_enabled,
                email_enabled=email_enabled,
                sms_enabled=sms_enabled,
                in_app_enabled=in_app_enabled,
                preferences=preferences
            )
            await self.session.commit()
            await self.session.refresh(pref)
            return pref