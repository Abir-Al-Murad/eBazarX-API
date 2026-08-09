from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_seller
from app.infrastructure.database.models import Seller
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.review import ReviewReplyCreate, ReviewReplyResponse
from app.application.services.review_service import ReviewService

router = APIRouter(
    prefix="/seller/reviews",
    tags=["Seller Reviews"],
    dependencies=[Depends(get_current_seller)]
)

@router.post("/{review_id}/reply", response_model=ReviewReplyResponse)
async def reply_to_review(
    review_id: UUID,
    data: ReviewReplyCreate,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    service = ReviewService(uow)
    try:
        reply = await service.reply_to_review(
            seller_id=current_seller.id,
            review_id=review_id,
            data=data
        )
        return reply
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))