from pydantic import BaseModel, ConfigDict, UUID4, Field
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID
from app.infrastructure.database.models import NotificationType

class NotificationBase(BaseModel):
    title: str
    body: str
    type: NotificationType
    image_url: Optional[str] = None
    action_url: Optional[str] = None

class NotificationResponse(NotificationBase):
    id: UUID
    user_id: UUID
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationUpdate(BaseModel):
    is_read: bool = True

class NotificationPreferencesBase(BaseModel):
    push_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True
    preferences: Optional[Dict] = None

class NotificationPreferencesResponse(NotificationPreferencesBase):
    user_id: UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationPreferencesUpdate(NotificationPreferencesBase):
    pass

class AdminBroadcastRequest(BaseModel):
    title: str
    body: str
    notification_type: NotificationType
    image_url: Optional[str] = None
    action_url: Optional[str] = None
    user_ids: Optional[List[UUID4]] = None  # If None, broadcast to all