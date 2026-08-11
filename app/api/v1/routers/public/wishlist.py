from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_customer
from app.infrastructure.database.models import User
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.wishlist import WishlistItemCreate, WishlistResponse
from app.application.services.wishlist_service import WishlistService

router = APIRouter(
    prefix="/customer/wishlist",
    tags=["Customer Wishlist"],
    dependencies=[Depends(get_current_customer)]
)

@router.get("/", response_model=WishlistResponse)
async def get_wishlist(
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = WishlistService(uow)
    wishlist = await service.get_wishlist(current_user.id)
    return wishlist

@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    data: WishlistItemCreate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = WishlistService(uow)
    try:
        await service.add_item(current_user.id, data.variant_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Item added to wishlist"}

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wishlist(
    item_id: UUID,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = WishlistService(uow)
    try:
        await service.remove_item(current_user.id, item_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return None


@router.delete("/variant/{variant_id}")
async def remove_from_wishlist_by_variant(
    variant_id: UUID,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    # Get the user's wishlist
    wishlist = await uow.wishlists.get_by_user(current_user.id)
    if not wishlist:
        raise HTTPException(404, "Wishlist not found")
    # Find the wishlist item with this variant
    item = await uow.wishlist_items.get_by_wishlist_and_variant(wishlist.id, variant_id)
    if not item:
        raise HTTPException(404, "Item not found in wishlist")
    await uow.wishlist_items.delete(item.id)
    await uow.commit()
    return {"message": "Removed from wishlist"}