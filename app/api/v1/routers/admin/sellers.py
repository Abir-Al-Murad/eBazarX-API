from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.models import SellerStatus
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.seller import (
    SellerStatusUpdate,
    SellerAdminDetailsResponse,
    SellerApplicationResponse
)
from app.application.services.seller_service import SellerService

router = APIRouter(
    prefix="/admin/sellers",
    tags=["Admin Sellers"],
    dependencies=[Depends(get_current_admin)]
)

@router.get("/", response_model=List[SellerAdminDetailsResponse])
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
    return sellers

@router.get("/pending", response_model=List[SellerAdminDetailsResponse])
async def list_pending_sellers(
    skip: int = 0,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_uow)
):
    sellers = await uow.sellers.get_by_status(SellerStatus.PENDING, skip, limit)
    return sellers

@router.get("/{seller_id}", response_model=SellerAdminDetailsResponse)
async def get_seller_details(
    seller_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    seller = await uow.sellers.get_by_id(seller_id)
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    return seller

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