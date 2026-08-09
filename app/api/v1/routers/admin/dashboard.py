from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.application.services.dashboard_service import DashboardService
from app.api.v1.schemas.dashboard import AdminDashboardStats, TopProduct, TopSeller

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin Dashboard"],
    dependencies=[Depends(get_current_admin)]
)

@router.get("/")
async def get_admin_dashboard(
    uow: UnitOfWork = Depends(get_uow)
):
    service = DashboardService(uow)
    try:
        stats = await service.get_admin_dashboard()
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/recent-orders")
async def get_admin_recent_orders(
    limit: int = 10,
    uow: UnitOfWork = Depends(get_uow)
):
    service = DashboardService(uow)
    try:
        orders = await service.get_admin_recent_orders(limit)
        return orders
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/top-sellers", response_model=List[TopSeller])
async def get_admin_top_sellers(
    limit: int = 5,
    uow: UnitOfWork = Depends(get_uow)
):
    service = DashboardService(uow)
    try:
        sellers = await service.get_admin_top_sellers(limit)
        return sellers
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/top-products", response_model=List[TopProduct])
async def get_admin_top_products(
    limit: int = 5,
    uow: UnitOfWork = Depends(get_uow)
):
    service = DashboardService(uow)
    try:
        products = await service.get_admin_top_products(limit)
        return products
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/revenue")
async def get_admin_revenue(
    days: int = 30,
    uow: UnitOfWork = Depends(get_uow)
):
    service = DashboardService(uow)
    try:
        revenue = await service.get_admin_revenue_by_period(days)
        return revenue
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))