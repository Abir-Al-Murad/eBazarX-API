from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_customer
from app.infrastructure.database.models import User
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse
from app.application.services.cart_service import CartService

router = APIRouter(
    prefix="/customer/cart",
    tags=["Customer Cart"],
    dependencies=[Depends(get_current_customer)]
)

@router.get("/", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = CartService(uow)
    cart = await service.get_cart(current_user.id)
    if not cart:
        return {"id": None, "items": [], "subtotal": 0, "total_items": 0}
    return cart

@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    data: CartItemCreate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = CartService(uow)
    try:
        await service.add_item(current_user.id, data.variant_id, data.quantity)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Item added"}

@router.put("/items/{item_id}")
async def update_cart_item(
    item_id: UUID,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = CartService(uow)
    try:
        await service.update_item(current_user.id, item_id, data.quantity)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Item updated"}

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    item_id: UUID,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = CartService(uow)
    try:
        await service.remove_item(current_user.id, item_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return None

@router.delete("/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = CartService(uow)
    await service.clear_cart(current_user.id)
    return None