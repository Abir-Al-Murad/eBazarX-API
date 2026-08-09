from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.v1.dependencies.auth import get_uow, get_current_user
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.coupon import CouponValidationRequest, CouponValidationResponse
from app.application.services.coupon_service import CouponService

router = APIRouter(prefix="/coupons", tags=["Public Coupons"])

@router.post("/validate", response_model=CouponValidationResponse)
async def validate_coupon(
    data: CouponValidationRequest,
    uow: UnitOfWork = Depends(get_uow)
):
    service = CouponService(uow)
    result = await service.validate_coupon(data.code, data.subtotal, data.user_id)
    return result