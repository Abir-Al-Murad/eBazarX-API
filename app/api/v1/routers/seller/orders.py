from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_seller
from app.infrastructure.database.models import Seller, OrderStatus
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.order import OrderItemResponse, OrderUpdateStatus

router = APIRouter(
    prefix="/seller/orders",
    tags=["Seller Orders"],
    dependencies=[Depends(get_current_seller)]
)

@router.get("/items", response_model=List[OrderItemResponse])
async def list_my_order_items(
    skip: int = 0,
    limit: int = 20,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    items = await uow.order_items.get_by_seller(current_seller.id, skip, limit)
    return items

@router.put("/items/{item_id}/status", response_model=OrderItemResponse)
async def update_order_item_status(
    item_id: UUID,
    data: OrderUpdateStatus,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    item = await uow.order_items.get(item_id)
    if not item or item.seller_id != current_seller.id:
        raise HTTPException(status_code=404, detail="Order item not found")
    # Validate status transition (optional)
    item.status = data.status
    await uow.commit()
    await uow.refresh(item)
    return item