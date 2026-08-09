from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.review import ReviewResponse, ReviewListResponse, ReviewStatisticsResponse
from app.application.services.review_service import ReviewService

router = APIRouter(prefix="/products/{product_id}/reviews", tags=["Public Reviews"])

@router.get("/", response_model=ReviewListResponse)
async def list_product_reviews(
    product_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|rating|likes)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    uow: UnitOfWork = Depends(get_uow)
):
    service = ReviewService(uow)
    result = await service.get_product_reviews(
        product_id=product_id,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return result

@router.get("/statistics", response_model=ReviewStatisticsResponse)
async def get_review_statistics(
    product_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    service = ReviewService(uow)
    stats = await service.get_review_statistics(product_id)
    return stats

@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review_details(
    product_id: UUID,
    review_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    # Ensure review belongs to product (optional check)
    service = ReviewService(uow)
    try:
        review = await service.get_review(review_id)
        if review.product_id != product_id:
            raise HTTPException(status_code=404, detail="Review not found")
        return review
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))