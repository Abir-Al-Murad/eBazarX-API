from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.flash_sale import FlashSaleCreate, FlashSaleUpdate, FlashSaleResponse
from app.application.services.flash_sale_service import FlashSaleService

router = APIRouter(
    prefix="/admin/flash-sales",
    tags=["Admin Flash Sales"],
    dependencies=[Depends(get_current_admin)]
)

@router.post("/", response_model=FlashSaleResponse, status_code=status.HTTP_201_CREATED)
async def create_flash_sale(
    data: FlashSaleCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    service = FlashSaleService(uow)
    try:
        flash_sale = await service.create_flash_sale(data)
        return flash_sale
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[FlashSaleResponse])
async def list_flash_sales(
    skip: int = 0,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_uow)
):
    flash_sales = await uow.flash_sales.get_all(skip, limit)
    return flash_sales

@router.get("/{flash_sale_id}", response_model=FlashSaleResponse)
async def get_flash_sale(
    flash_sale_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    flash_sale = await uow.flash_sales.get(flash_sale_id)
    if not flash_sale:
        raise HTTPException(status_code=404, detail="Flash sale not found")
    return flash_sale

@router.put("/{flash_sale_id}", response_model=FlashSaleResponse)
async def update_flash_sale(
    flash_sale_id: UUID,
    data: FlashSaleUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    service = FlashSaleService(uow)
    try:
        flash_sale = await service.update_flash_sale(flash_sale_id, data)
        return flash_sale
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{flash_sale_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flash_sale(
    flash_sale_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    service = FlashSaleService(uow)
    await service.delete_flash_sale(flash_sale_id)
    return None