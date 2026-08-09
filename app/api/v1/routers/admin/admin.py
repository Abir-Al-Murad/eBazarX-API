from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.infrastructure.database.models import WithdrawStatus

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(get_current_admin)])

@router.get("/dashboard")
async def admin_dashboard():
    return {"message": "Admin dashboard"}

@router.get("/withdrawals")
async def list_withdrawals(
    skip: int = 0,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_uow)
):
    requests = await uow.withdraw_requests.get_all(skip, limit)
    return requests

@router.put("/withdrawals/{request_id}")
async def update_withdrawal(
    request_id: UUID4,
    status: WithdrawStatus,
    admin_notes: Optional[str] = None,
    uow: UnitOfWork = Depends(get_uow)
):
    request = await uow.withdraw_requests.get(request_id)
    if not request:
        raise HTTPException(404, "Not found")
    request.status = status
    request.admin_notes = admin_notes
    if status in (WithdrawStatus.APPROVED, WithdrawStatus.COMPLETED):
        request.processed_at = datetime.now(timezone.utc)
    await uow.commit()
    return {"message": "Updated"}