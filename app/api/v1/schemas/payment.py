from pydantic import BaseModel, ConfigDict, UUID4, Field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID
from app.infrastructure.database.models import PaymentGateway, PaymentStatus

class PaymentInitiateRequest(BaseModel):
    order_id: UUID4
    gateway: PaymentGateway
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PaymentInitiateResponse(BaseModel):
    payment_id: UUID
    order_id: UUID
    gateway: PaymentGateway
    redirect_url: Optional[str] = None
    transaction_id: Optional[str] = None
    

class PaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    gateway: PaymentGateway
    amount: Decimal
    currency: str
    transaction_id: Optional[str]
    status: PaymentStatus
    paid_at: Optional[datetime]
    gateway_response: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaymentWebhookRequest(BaseModel):
    gateway: PaymentGateway
    payload: Dict[str, Any]

class PaymentWebhookPayload(BaseModel):
    order_id: UUID4
    transaction_id: str
    status: PaymentStatus
    gateway_data: Optional[dict] = None
    
class RefundRequest(BaseModel):
    payment_id: UUID4
    amount: Decimal
    reason: Optional[str] = None

class RefundResponse(BaseModel):
    id: UUID
    payment_id: UUID
    order_id: UUID
    amount: Decimal
    reason: Optional[str]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)