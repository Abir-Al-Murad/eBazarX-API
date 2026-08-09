from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.brand import BrandResponse

router = APIRouter(prefix="/brands", tags=["Public Brands"])

@router.get("/", response_model=List[BrandResponse])
async def list_brands(
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow)
):
    brands = await uow.brands.get_all(skip, limit)
    return brands

@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    brand = await uow.brands.get(brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return brand