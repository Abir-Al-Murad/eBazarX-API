from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.order import OrderResponse, OrderUpdateStatus, OrderUpdatePaymentStatus
from app.infrastructure.database.models import OrderStatus, PaymentStatus

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
    # Use repository method with status filter if available, else filter in Python
    orders = await uow.orders.get_all(skip, limit)
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

# ============================================================
# ✅ NEW: Update Payment Status (Admin only)
# ============================================================
@router.put("/{order_id}/payment-status", response_model=OrderResponse)
async def update_order_payment_status(
    order_id: UUID,
    data: OrderUpdatePaymentStatus,
    uow: UnitOfWork = Depends(get_uow)
):
    order = await uow.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    old_status = order.payment_status
    order.payment_status = data.payment_status
    
    # Optionally, if payment becomes 'paid', we can also update order_status to 'processing'
    if data.payment_status == PaymentStatus.PAID and old_status != PaymentStatus.PAID:
        order.order_status = OrderStatus.PROCESSING
        # Release reserved stock and deduct actual stock for each order item
        # (This is usually done by the payment service, but we include it here for consistency)
        order_items = await uow.order_items.get_by_order(order_id)
        for item in order_items:
            variant = await uow.variants.get(item.variant_id)
            if variant:
                variant.stock -= item.quantity
                variant.reserved_stock -= item.quantity
    
    await uow.commit()
    await uow.refresh(order)
    return order