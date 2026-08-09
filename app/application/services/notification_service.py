from uuid import UUID
from typing import Optional, List, Dict, Any
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.infrastructure.database.models import Notification, NotificationType, User

class NotificationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def send_notification(
        self,
        user_id: UUID,
        title: str,
        body: str,
        notification_type: NotificationType,
        image_url: Optional[str] = None,
        action_url: Optional[str] = None
    ) -> Notification:
        """Send an in-app notification to a user."""
        # Check if user exists
        user = await self.uow.users.get(user_id)
        if not user:
            raise BusinessError("User not found")

        # Check notification preferences (if disabled, we may still save but not send push/email)
        pref = await self.uow.notification_preferences.get_by_user(user_id)
        if pref and not pref.in_app_enabled:
            # In-app disabled, we might still save for history
            # For now, we still save
            pass

        notification = await self.uow.notifications.create(
            user_id=user_id,
            title=title,
            body=body,
            type=notification_type,
            image_url=image_url,
            action_url=action_url,
            is_read=False
        )
        await self.uow.commit()
        await self.uow.refresh(notification)

        # Trigger push/email/SMS if enabled (async via Celery)
        if pref:
            if pref.push_enabled:
                # Send push notification (async task)
                pass
            if pref.email_enabled:
                # Send email (async task)
                pass
            if pref.sms_enabled:
                # Send SMS (async task)
                pass

        return notification

    async def send_bulk_notification(
        self,
        user_ids: List[UUID],
        title: str,
        body: str,
        notification_type: NotificationType,
        image_url: Optional[str] = None,
        action_url: Optional[str] = None
    ) -> List[Notification]:
        """Send notification to multiple users."""
        notifications = []
        for user_id in user_ids:
            try:
                notif = await self.send_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    image_url=image_url,
                    action_url=action_url
                )
                notifications.append(notif)
            except Exception:
                # Log error but continue for other users
                continue
        return notifications

    async def send_order_notification(self, user_id: UUID, order_id: UUID, status: str):
        """Helper: send order status notification."""
        title = f"Order #{order_id.hex[:8]} {status}"
        body = f"Your order status has been updated to {status}"
        await self.send_notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=NotificationType.ORDER,
            action_url=f"/orders/{order_id}"
        )

    async def send_payment_notification(self, user_id: UUID, payment_id: UUID, status: str):
        """Helper: send payment notification."""
        title = f"Payment {status}"
        body = f"Your payment #{payment_id.hex[:8]} has been {status}"
        await self.send_notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=NotificationType.PAYMENT,
            action_url=f"/payments/{payment_id}"
        )