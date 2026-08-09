from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.product import ProductResponse
from app.infrastructure.database.models import ProductApprovalStatus

router = APIRouter(prefix="/products", tags=["Public Products"])

@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    uow: UnitOfWork = Depends(get_uow)
):
    products = await uow.products.get_all(
        skip=skip,
        limit=limit,
        category_id=category_id,
        search=search,
        is_active=True,
        approval_status=ProductApprovalStatus.APPROVED
    )
    # Eagerly load variants and images? We'll rely on lazy loading in response serialization.
    return products

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    product = await uow.products.get(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if not product.is_active or product.approval_status != ProductApprovalStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not available")
    return product