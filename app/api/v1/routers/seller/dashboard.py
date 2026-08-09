from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_seller
from app.infrastructure.database.models import Seller
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.application.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/seller/dashboard",
    tags=["Seller Dashboard"],
    dependencies=[Depends(get_current_seller)]
)

@router.get("/")
async def get_seller_dashboard(
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    service = DashboardService(uow)
    try:
        stats = await service.get_seller_dashboard(current_seller.id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/order-status")
async def get_seller_order_status(
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    service = DashboardService(uow)
    try:
        stats = await service.get_seller_order_status_count(current_seller.id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/top-products")
async def get_seller_top_products(
    limit: int = 5,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    service = DashboardService(uow)
    try:
        products = await service.get_seller_top_products(current_seller.id, limit)
        return products
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))