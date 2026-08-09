from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.product import ProductResponse, ProductApprovalUpdate
from app.infrastructure.database.models import ProductApprovalStatus

router = APIRouter(
    prefix="/admin/products",
    tags=["Admin Products"],
    dependencies=[Depends(get_current_admin)]
)

@router.get("/", response_model=List[ProductResponse])
async def list_all_products(
    skip: int = 0,
    limit: int = 20,
    approval_status: Optional[ProductApprovalStatus] = None,
    uow: UnitOfWork = Depends(get_uow)
):
    products = await uow.products.get_all(
        skip=skip,
        limit=limit,
        approval_status=approval_status,
        is_active=None  # Include all (both active and inactive)
    )
    return products

@router.get("/pending", response_model=List[ProductResponse])
async def list_pending_products(
    skip: int = 0,
    limit: int = 20,
    uow: UnitOfWork = Depends(get_uow)
):
    products = await uow.products.get_pending_products(skip, limit)
    return products

@router.put("/{product_id}/approval", response_model=ProductResponse)
async def update_product_approval(
    product_id: UUID,
    data: ProductApprovalUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    product = await uow.products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.approval_status = data.approval_status
    if data.approval_status == ProductApprovalStatus.APPROVED:
        product.is_active = True
    elif data.approval_status in (ProductApprovalStatus.REJECTED, ProductApprovalStatus.ARCHIVED):
        product.is_active = False

    # Optionally store notes (we don't have a field for notes, could add or log)
    await uow.commit()
    await uow.refresh(product)
    return product