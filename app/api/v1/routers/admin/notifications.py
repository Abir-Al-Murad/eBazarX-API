from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.notification import AdminBroadcastRequest, NotificationResponse
from app.application.services.notification_service import NotificationService
from app.infrastructure.database.models import User

router = APIRouter(
    prefix="/admin/notifications",
    tags=["Admin Notifications"],
    dependencies=[Depends(get_current_admin)]
)

@router.post("/broadcast", response_model=List[NotificationResponse], status_code=status.HTTP_201_CREATED)
async def broadcast_notification(
    data: AdminBroadcastRequest,
    uow: UnitOfWork = Depends(get_uow)
):
    """Send notification to all users or specific user."""
    service = NotificationService(uow)

    # Get user IDs
    if data.user_ids:
        user_ids = data.user_ids
    else:
        # Get all users
        users = await uow.users.get_all()
        user_ids = [user.id for user in users]

    if not user_ids:
        raise HTTPException(status_code=400, detail="No users found")

    notifications = await service.send_bulk_notification(
        user_ids=user_ids,
        title=data.title,
        body=data.body,
        notification_type=data.notification_type,
        image_url=data.image_url,
        action_url=data.action_url
    )
    return notifications