from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_current_user, get_uow
from app.api.v1.dependencies.permissions import get_current_customer
from app.api.v1.dependencies.services import get_order_service
from app.infrastructure.database.models import OrderStatus, User
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.order import OrderCreate, OrderPlaceResponse, OrderResponse
from app.application.services.order_service import OrderService

router = APIRouter(
    prefix="/customer/orders",
    tags=["Customer Orders"],
    dependencies=[Depends(get_current_customer)]
)

@router.post("/", response_model=OrderPlaceResponse)
async def place_order(
    order_data: OrderCreate,
    current_user=Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.place_order(
        user_id=current_user.id,
        address_id=order_data.address_id,
        items=[
            {
                "variant_id": item.variant_id,
                "quantity": item.quantity,
            }
            for item in order_data.items
        ],
        payment_method=order_data.payment_method,
        coupon_code=order_data.coupon_code,
        notes=order_data.notes,
        success_url=order_data.success_url,
        cancel_url=order_data.cancel_url,
    )

@router.get("/", response_model=List[OrderResponse])
async def list_my_orders(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    orders = await uow.orders.get_by_user(current_user.id, skip, limit)
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    order = await uow.orders.get_with_items(order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    order = await uow.orders.get(order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.order_status not in (OrderStatus.PENDING, OrderStatus.PROCESSING):
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")

    # ✅ Release reserved stock for each item
    order_items = await uow.order_items.get_by_order(order_id)
    for item in order_items:
        variant = await uow.variants.get(item.variant_id)
        if variant:
            variant.reserved_stock -= item.quantity

    order.order_status = OrderStatus.CANCELLED
    await uow.commit()
    await uow.refresh(order)
    return order