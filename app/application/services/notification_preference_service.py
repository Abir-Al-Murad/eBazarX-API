from uuid import UUID
from typing import Optional, Dict
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError

class NotificationPreferenceService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_preferences(self, user_id: UUID):
        pref = await self.uow.notification_preferences.get_by_user(user_id)
        if not pref:
            # Create default preferences
            pref = await self.uow.notification_preferences.create(
                user_id=user_id,
                push_enabled=True,
                email_enabled=True,
                sms_enabled=False,
                in_app_enabled=True,
                preferences={}
            )
            await self.uow.commit()
            await self.uow.refresh(pref)
        return pref

    async def update_preferences(
        self,
        user_id: UUID,
        push_enabled: Optional[bool] = None,
        email_enabled: Optional[bool] = None,
        sms_enabled: Optional[bool] = None,
        in_app_enabled: Optional[bool] = None,
        preferences: Optional[Dict] = None
    ):
        pref = await self.get_preferences(user_id)
        if push_enabled is not None:
            pref.push_enabled = push_enabled
        if email_enabled is not None:
            pref.email_enabled = email_enabled
        if sms_enabled is not None:
            pref.sms_enabled = sms_enabled
        if in_app_enabled is not None:
            pref.in_app_enabled = in_app_enabled
        if preferences is not None:
            pref.preferences = preferences
        await self.uow.commit()
        await self.uow.refresh(pref)
        return pref