from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_customer
from app.infrastructure.database.models import OrderStatus, User
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.order import OrderCreate, OrderResponse
from app.application.services.order_service import OrderService

router = APIRouter(
    prefix="/customer/orders",
    tags=["Customer Orders"],
    dependencies=[Depends(get_current_customer)]
)

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = OrderService(uow)
    try:
        order = await service.place_order(
            user_id=current_user.id,
            address_id=data.address_id,
            items=[item.model_dump() for item in data.items],
            coupon_code=data.coupon_code,
            notes=data.notes
        )
        return order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
    order.order_status = OrderStatus.CANCELLED
    # Optionally release reserved stock
    await uow.commit()
    await uow.refresh(order)
    return order