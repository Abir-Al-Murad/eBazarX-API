import uuid

from click import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from app.api.v1.dependencies.auth import get_current_user, get_uow
from app.api.v1.dependencies.permissions import get_current_seller
from app.api.v1.schemas.seller import PublicSellerProfileResponse, SellerApplicationCreate, SellerApplicationResponse, SellerProfileUpdate
from app.application.services.seller_service import SellerService
from app.infrastructure.database.models import OrderStatus, Seller, SellerStatus, User
from app.application.services.product_service import ProductService
from app.api.v1.schemas.product import ProductCreate
from app.api.v1.dependencies.services import get_order_item_repo, get_product_service
from app.infrastructure.database.repositories.order_item_repository import OrderItemRepository
from app.infrastructure.database.unit_of_work import UnitOfWork

router = APIRouter(prefix="/seller", tags=["Seller"], dependencies=[Depends(get_current_seller)])
apply_router = APIRouter(prefix="/seller/apply", tags=["Seller Application"], dependencies=[Depends(get_current_user)])

@router.post("/products")
async def create_product(
    product_data: ProductCreate,
    current_seller: Seller = Depends(get_current_seller),
    product_service: ProductService = Depends(get_product_service)
):
    try:
        product = await product_service.create_product(current_seller.id, product_data)
        return {"id": product.id, "message": "Product created pending approval"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/orders")
async def seller_orders(
    skip: int = 0,
    limit: int = 20,
    current_seller: Seller = Depends(get_current_seller),
    order_item_repo: OrderItemRepository = Depends(get_order_item_repo)
):
    items = await order_item_repo.get_by_seller(current_seller.id, skip, limit)
    return items

@router.put("/orders/{order_item_id}/status")
async def update_order_item_status(
    order_item_id: UUID4,
    status: OrderStatus,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    item = await uow.order_items.get(order_item_id)
    if not item or item.seller_id != current_seller.id:
        raise HTTPException(404, "Order item not found")
    item.status = status
    await uow.commit()
    return {"message": "Status updated"}

@apply_router.post("/", response_model=SellerApplicationResponse, status_code=201)
async def apply_seller(
    data: SellerApplicationCreate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    service = SellerService(uow)
    try:
        seller = await service.apply_seller(current_user.id, data)
        return seller
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/me", response_model=SellerApplicationResponse)
async def get_my_seller_profile(
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    """Get the authenticated seller's own profile."""
    service = SellerService(uow)
    seller = await service.get_seller_profile(current_seller.id)
    if not seller:
        raise HTTPException(status_code=404, detail="Seller profile not found")
    return seller

@router.put("/me", response_model=SellerApplicationResponse)
async def update_my_seller_profile(
    data: SellerProfileUpdate,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    """Update the authenticated seller's own profile."""
    service = SellerService(uow)
    # Only update allowed fields (exclude sensitive ones like status, commission_rate)
    update_data = data.model_dump(exclude_unset=True)
    # Ensure shop_slug uniqueness (if changed)
    if "shop_slug" in update_data:
        existing = await uow.sellers.get_by_slug(update_data["shop_slug"])
        if existing and existing.id != current_seller.id:
            raise HTTPException(status_code=409, detail="Shop slug already taken")
    updated = await service.update_seller_profile(current_seller.id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Seller profile not found")
    return updated

# ============================================================
# PUBLIC SELLER PROFILE
# ============================================================

public_router = APIRouter(prefix="/public/sellers", tags=["Public Sellers"])
    
@public_router.get("/{seller_id}", response_model=PublicSellerProfileResponse)
async def get_public_seller_profile(
    seller_id: uuid.UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    """Publicly view a seller's shop profile."""
    service = SellerService(uow)
    seller = await service.get_seller_profile(seller_id)
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    if seller.status != SellerStatus.APPROVED:
        raise HTTPException(status_code=404, detail="Shop not available")
    return seller