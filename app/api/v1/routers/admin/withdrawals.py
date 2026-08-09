from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.api.v1.schemas.wallet import WithdrawalRequestResponse, WithdrawalRequestUpdate
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.application.services.wallet_service import WalletService

router = APIRouter(
    prefix="/admin/withdrawals",
    tags=["Admin Withdrawals"],
    dependencies=[Depends(get_current_admin)]
)

@router.get("/", response_model=List[WithdrawalRequestResponse])
async def list_withdrawals(
    skip: int = 0,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_uow)
):
    requests = await uow.withdraw_requests.get_all(skip, limit)
    return requests

@router.get("/pending", response_model=List[WithdrawalRequestResponse])
async def list_pending_withdrawals(
    skip: int = 0,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_uow)
):
    from app.infrastructure.database.models import WithdrawStatus
    requests = await uow.withdraw_requests.get_by_status(WithdrawStatus.PENDING, skip, limit)
    return requests

@router.put("/{request_id}", response_model=WithdrawalRequestResponse)
async def process_withdrawal(
    request_id: UUID,
    data: WithdrawalRequestUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    service = WalletService(uow)
    try:
        request = await service.process_withdrawal(request_id, data.status, data.admin_notes)
        return request
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))