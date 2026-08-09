from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.order import OrderResponse, OrderUpdateStatus
from app.infrastructure.database.models import OrderStatus

router = APIRouter(
    prefix="/admin/orders",
    tags=["Admin Orders"],
    dependencies=[Depends(get_current_admin)]
)

@router.get("/", response_model=List[OrderResponse])
async def list_all_orders(
    skip: int = 0,
    limit: int = 20,
    status: Optional[OrderStatus] = None,
    uow: UnitOfWork = Depends(get_uow)
):
    # We need a method to filter by status; we'll add a method in OrderRepository
    orders = await uow.orders.get_all(skip, limit)  # For now, we just get all
    # We can filter in Python; better to implement in repository.
    if status:
        orders = [o for o in orders if o.order_status == status]
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_details(
    order_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    order = await uow.orders.get_with_items(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    data: OrderUpdateStatus,
    uow: UnitOfWork = Depends(get_uow)
):
    order = await uow.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.order_status = data.status
    await uow.commit()
    await uow.refresh(order)
    return order