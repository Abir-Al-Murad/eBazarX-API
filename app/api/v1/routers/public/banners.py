from fastapi import APIRouter, Depends
from typing import List
from app.api.v1.dependencies.auth import get_uow
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.banner import BannerResponse
from datetime import datetime, timezone

router = APIRouter(prefix="/banners", tags=["Public Banners"])

@router.get("/", response_model=List[BannerResponse])
async def list_active_banners(
    uow: UnitOfWork = Depends(get_uow)
):
    banners = await uow.banners.get_active_banners(datetime.now(timezone.utc))
    return banners