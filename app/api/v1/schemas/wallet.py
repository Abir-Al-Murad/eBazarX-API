from pydantic import BaseModel, ConfigDict, Field, UUID4
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from app.infrastructure.database.models import WalletTransactionType, WithdrawStatus

class WalletResponse(BaseModel):
    seller_id: UUID
    available_balance: Decimal = Decimal(0)
    pending_balance: Decimal = Decimal(0)
    locked_balance: Decimal = Decimal(0)
    withdrawn_total: Decimal = Decimal(0)
    lifetime_earnings: Decimal = Decimal(0)
    commission_paid: Decimal = Decimal(0)

    model_config = ConfigDict(from_attributes=True)

class WalletTransactionResponse(BaseModel):
    id: UUID
    type: WalletTransactionType
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    description: Optional[str]
    reference_id: Optional[UUID]
    reference_type: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WithdrawalRequestCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    method: str = Field(..., max_length=50)  # bank, bkash, nagad, etc.
    account_info: dict = Field(..., description="Account details (e.g. bank, account number, mobile)")

class WithdrawalRequestUpdate(BaseModel):
    status: WithdrawStatus
    admin_notes: Optional[str] = None

class WithdrawalRequestResponse(BaseModel):
    id: UUID
    seller_id: UUID
    amount: Decimal
    method: str
    account_info: dict
    status: WithdrawStatus
    admin_notes: Optional[str]
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)