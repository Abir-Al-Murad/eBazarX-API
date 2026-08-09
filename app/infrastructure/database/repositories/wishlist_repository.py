from sqlalchemy import select
from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.models import Wishlist, WishlistItem
from .base import AsyncBaseRepository

class WishlistRepository(AsyncBaseRepository[Wishlist]):
    async def get_by_user(self, user_id: UUID) -> Optional[Wishlist]:
        result = await self.session.execute(
            select(Wishlist).filter(Wishlist.user_id == user_id)
        )
        return result.scalar_one_or_none()

class WishlistItemRepository(AsyncBaseRepository[WishlistItem]):
    async def get_by_wishlist(self, wishlist_id: UUID) -> Sequence[WishlistItem]:
        result = await self.session.execute(
            select(WishlistItem).filter(WishlistItem.wishlist_id == wishlist_id)
        )
        return result.scalars().all()

    async def get_by_wishlist_and_variant(self, wishlist_id: UUID, variant_id: UUID) -> Optional[WishlistItem]:
        result = await self.session.execute(
            select(WishlistItem).filter(
                WishlistItem.wishlist_id == wishlist_id,
                WishlistItem.variant_id == variant_id
            )
        )
        return result.scalar_one_or_none()