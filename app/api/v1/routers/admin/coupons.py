from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.coupon import CouponCreate, CouponUpdate, CouponResponse
from app.application.services.coupon_service import CouponService

router = APIRouter(
    prefix="/admin/coupons",
    tags=["Admin Coupons"],
    dependencies=[Depends(get_current_admin)]
)

@router.post("/", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_coupon(
    data: CouponCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    service = CouponService(uow)
    try:
        coupon = await service.create_coupon(
            seller_id=data.seller_id,  # Can be null for platform coupons
            data=data,
            product_ids=data.product_ids,
            category_ids=data.category_ids
        )
        return coupon
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[CouponResponse])
async def list_all_coupons(
    skip: int = 0,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_uow)
):
    coupons = await uow.coupons.get_all(skip, limit)
    return coupons

@router.get("/{coupon_id}", response_model=CouponResponse)
async def get_coupon(
    coupon_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    coupon = await uow.coupons.get(coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return coupon

@router.put("/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    coupon_id: UUID,
    data: CouponUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    service = CouponService(uow)
    try:
        updated = await service.update_coupon(coupon_id, data)
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coupon(
    coupon_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    service = CouponService(uow)
    await service.delete_coupon(coupon_id)
    return None