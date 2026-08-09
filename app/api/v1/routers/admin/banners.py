from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.banner import BannerCreate, BannerUpdate, BannerResponse
from app.application.services.banner_service import BannerService

router = APIRouter(
    prefix="/admin/banners",
    tags=["Admin Banners"],
    dependencies=[Depends(get_current_admin)]
)

@router.post("/", response_model=BannerResponse, status_code=status.HTTP_201_CREATED)
async def create_banner(
    data: BannerCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    service = BannerService(uow)
    try:
        banner = await service.create_banner(data)
        return banner
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[BannerResponse])
async def list_banners(
    skip: int = 0,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_uow)
):
    banners = await uow.banners.get_all(skip, limit)
    return banners

@router.get("/{banner_id}", response_model=BannerResponse)
async def get_banner(
    banner_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    banner = await uow.banners.get(banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    return banner

@router.put("/{banner_id}", response_model=BannerResponse)
async def update_banner(
    banner_id: UUID,
    data: BannerUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    service = BannerService(uow)
    try:
        banner = await service.update_banner(banner_id, data)
        return banner
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_banner(
    banner_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    service = BannerService(uow)
    await service.delete_banner(banner_id)
    return None