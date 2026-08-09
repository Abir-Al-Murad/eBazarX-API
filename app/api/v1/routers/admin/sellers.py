from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.models import SellerStatus
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.seller import SellerStatusUpdate, SellerAdminListResponse, SellerApplicationResponse
from app.application.services.seller_service import SellerService

router = APIRouter(
    prefix="/admin/sellers",
    tags=["Admin Sellers"],
    dependencies=[Depends(get_current_admin)]
)

@router.get("/", response_model=List[SellerAdminListResponse])
async def list_sellers(
    status: Optional[SellerStatus] = Query(None, description="Filter by status"),
    skip: int = 0,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_uow)
):
    if status:
        sellers = await uow.sellers.get_by_status(status, skip, limit)
    else:
        sellers = await uow.sellers.get_all(skip, limit)
    # Optionally enrich with user email/phone (we need to join or select)
    # For now, return as-is; you can later add a join query in repository
    return sellers

@router.get("/pending", response_model=List[SellerAdminListResponse])
async def list_pending_sellers(
    skip: int = 0,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_uow)
):
    sellers = await uow.sellers.get_by_status(SellerStatus.PENDING, skip, limit)
    return sellers

@router.put("/{seller_id}/status", response_model=SellerApplicationResponse)
async def update_seller_status(
    seller_id: UUID,
    data: SellerStatusUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    service = SellerService(uow)
    try:
        seller = await service.update_status(seller_id, data.status, data.admin_notes)
        return seller
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))