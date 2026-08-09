from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from app.api.v1.dependencies.auth import get_current_user, get_uow
from app.api.v1.dependencies.permissions import get_current_seller
from app.api.v1.schemas.seller import SellerApplicationCreate, SellerApplicationResponse
from app.application.services.seller_service import SellerService
from app.infrastructure.database.models import OrderStatus, Seller, User
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