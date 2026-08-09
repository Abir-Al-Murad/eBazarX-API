from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_customer
from app.infrastructure.database.models import User
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse,
    ReviewVoteCreate, ReviewReportCreate, ReviewReportResponse
)
from app.application.services.review_service import ReviewService

router = APIRouter(
    prefix="/customer/reviews",
    tags=["Customer Reviews"],
    dependencies=[Depends(get_current_customer)]
)

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = ReviewService(uow)
    try:
        review = await service.create_review(
            user_id=current_user.id,
            data=data,
            image_urls=data.images
        )
        return review
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    data: ReviewUpdate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = ReviewService(uow)
    try:
        review = await service.update_review(
            user_id=current_user.id,
            review_id=review_id,
            data=data,
            image_urls=data.images
        )
        return review
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = ReviewService(uow)
    try:
        await service.delete_review(current_user.id, review_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{review_id}/vote", status_code=status.HTTP_200_OK)
async def vote_review(
    review_id: UUID,
    data: ReviewVoteCreate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = ReviewService(uow)
    try:
        result = await service.vote_review(
            user_id=current_user.id,
            review_id=review_id,
            data=data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{review_id}/report", response_model=ReviewReportResponse)
async def report_review(
    review_id: UUID,
    data: ReviewReportCreate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = ReviewService(uow)
    try:
        report = await service.report_review(
            user_id=current_user.id,
            review_id=review_id,
            data=data
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))