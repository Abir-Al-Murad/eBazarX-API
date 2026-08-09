from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_customer
from app.infrastructure.database.models import User
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.notification import (
    NotificationResponse,
    NotificationUpdate,
    NotificationPreferencesUpdate,
    NotificationPreferencesResponse
)
from app.application.services.notification_service import NotificationService
from app.application.services.notification_preference_service import NotificationPreferenceService

router = APIRouter(
    prefix="/customer/notifications",
    tags=["Customer Notifications"],
    dependencies=[Depends(get_current_customer)]
)

# ----- Notification Endpoints -----
@router.get("/", response_model=List[NotificationResponse])
async def get_my_notifications(
    skip: int = 0,
    limit: int = 20,
    is_read: Optional[bool] = None,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    notifications = await uow.notifications.get_by_user(current_user.id, skip, limit, is_read)
    return notifications

@router.get("/unread-count", response_model=int)
async def get_unread_count(
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    count = await uow.notifications.count_unread(current_user.id)
    return count

@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    notification = await uow.notifications.mark_as_read(notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.put("/mark-all-read")
async def mark_all_as_read(
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    count = await uow.notifications.mark_all_as_read(current_user.id)
    return {"message": f"{count} notifications marked as read"}

# ----- Notification Preferences -----
@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = NotificationPreferenceService(uow)
    pref = await service.get_preferences(current_user.id)
    return pref

@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    data: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = NotificationPreferenceService(uow)
    pref = await service.update_preferences(
        user_id=current_user.id,
        push_enabled=data.push_enabled,
        email_enabled=data.email_enabled,
        sms_enabled=data.sms_enabled,
        in_app_enabled=data.in_app_enabled,
        preferences=data.preferences
    )
    return pref