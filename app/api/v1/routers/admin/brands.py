from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime, timezone
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.brand import BrandCreate, BrandUpdate, BrandResponse

router = APIRouter(
    prefix="/admin/brands",
    tags=["Admin Brands"],
    dependencies=[Depends(get_current_admin)]
)

@router.post("/", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    data: BrandCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    if await uow.brands.check_slug_exists(data.slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Brand with slug '{data.slug}' already exists"
        )

    brand = await uow.brands.create(
        name=data.name,
        slug=data.slug,
        logo=data.logo,
        description=data.description,
        is_active=True
    )
    await uow.commit()
    await uow.refresh(brand)
    return brand

@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    data: BrandUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    brand = await uow.brands.get(brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    if data.slug is not None:
        if await uow.brands.check_slug_exists(data.slug, exclude_id=brand_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Brand with slug '{data.slug}' already exists"
            )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(brand, key, value)

    await uow.commit()
    await uow.refresh(brand)
    return brand

@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    brand = await uow.brands.get(brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    brand.deleted_at = datetime.now(timezone.utc)
    await uow.commit()
    return None