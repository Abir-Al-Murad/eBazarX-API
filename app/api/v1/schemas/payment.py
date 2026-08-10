from pydantic import BaseModel, UUID4
from decimal import Decimal
from typing import Optional
from datetime import datetime
from app.infrastructure.database.models import PaymentGateway, PaymentStatus

class PaymentInitiateRequest(BaseModel):
    order_id: UUID4
    gateway: PaymentGateway  # ✅ Add this field
    success_url: str
    cancel_url: str

class PaymentInitiateResponse(BaseModel):
    payment_id: UUID4
    order_id: UUID4
    gateway: PaymentGateway
    redirect_url: str
    transaction_id: Optional[str]

class PaymentResponse(BaseModel):
    id: UUID4
    order_id: UUID4
    gateway: PaymentGateway
    amount: Decimal
    currency: str
    transaction_id: Optional[str]
    status: PaymentStatus
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
class PaymentWebhookPayload(BaseModel):
    """SSLCommerz webhook/redirect payload."""
    val_id: Optional[str] = None
    tran_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[str] = None
    store_amount: Optional[str] = None
    card_type: Optional[str] = None
    card_no: Optional[str] = None
    bank_tran_id: Optional[str] = None
    # Add any other fields SSLCommerz sends