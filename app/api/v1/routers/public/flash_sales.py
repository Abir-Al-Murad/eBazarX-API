from fastapi import APIRouter, Depends
from typing import List
from app.api.v1.dependencies.auth import get_uow
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.flash_sale import FlashSaleResponse
from datetime import datetime, timezone

router = APIRouter(prefix="/flash-sales", tags=["Public Flash Sales"])

@router.get("/", response_model=List[FlashSaleResponse])
async def list_active_flash_sales(
    uow: UnitOfWork = Depends(get_uow)
):
    flash_sales = await uow.flash_sales.get_active_flash_sales(datetime.now(timezone.utc))
    return flash_sales