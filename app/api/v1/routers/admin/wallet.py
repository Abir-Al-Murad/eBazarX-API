from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.models import WithdrawStatus
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.wallet import WithdrawalRequestResponse, WithdrawalRequestUpdate
from app.application.services.wallet_service import WalletService

router = APIRouter(
    prefix="/admin/wallet",
    tags=["Admin Wallet"],
    dependencies=[Depends(get_current_admin)]
)

@router.get("/withdrawals", response_model=List[WithdrawalRequestResponse])
async def list_withdrawals(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    uow: UnitOfWork = Depends(get_uow)
):
    if status:
        from app.infrastructure.database.models import WithdrawStatus
        try:
            status_enum = WithdrawStatus(status)
            withdrawals = await uow.withdraw_requests.get_by_status(status_enum, skip, limit)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    else:
        withdrawals = await uow.withdraw_requests.get_all(skip, limit)
    return withdrawals

@router.put("/withdrawals/{withdrawal_id}", response_model=WithdrawalRequestResponse)
async def process_withdrawal(
    withdrawal_id: UUID,
    data: WithdrawalRequestUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    service = WalletService(uow)
    try:
        if data.status == WithdrawStatus.COMPLETED:
            withdrawal = await service.approve_withdrawal(withdrawal_id, data.admin_notes)
        elif data.status == WithdrawStatus.REJECTED:
            withdrawal = await service.reject_withdrawal(withdrawal_id, data.admin_notes)
        else:
            raise HTTPException(status_code=400, detail="Invalid status update")
        return withdrawal
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))