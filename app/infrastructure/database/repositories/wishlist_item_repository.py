from sqlalchemy import select, delete
from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.models import WishlistItem
from .base import AsyncBaseRepository

class WishlistItemRepository(AsyncBaseRepository[WishlistItem]):
    """Repository for WishlistItem model."""
    
    async def get(self, id: UUID) -> Optional[WishlistItem]:
        """Get a wishlist item by ID."""
        result = await self.session.execute(
            select(WishlistItem).filter(WishlistItem.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_wishlist(self, wishlist_id: UUID) -> Sequence[WishlistItem]:
        """Get all items in a wishlist."""
        result = await self.session.execute(
            select(WishlistItem).filter(WishlistItem.wishlist_id == wishlist_id)
        )
        return result.scalars().all()

    async def get_by_wishlist_and_variant(
        self, wishlist_id: UUID, variant_id: UUID
    ) -> Optional[WishlistItem]:
        """Get a specific wishlist item by wishlist and variant."""
        result = await self.session.execute(
            select(WishlistItem).filter(
                WishlistItem.wishlist_id == wishlist_id,
                WishlistItem.variant_id == variant_id
            )
        )
        return result.scalar_one_or_none()

    async def delete_by_wishlist_and_variant(
        self, wishlist_id: UUID, variant_id: UUID
    ) -> bool:
        """Delete a wishlist item by wishlist and variant."""
        stmt = delete(WishlistItem).where(
            WishlistItem.wishlist_id == wishlist_id,
            WishlistItem.variant_id == variant_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def count_by_wishlist(self, wishlist_id: UUID) -> int:
        """Count items in a wishlist."""
        result = await self.session.execute(
            select(WishlistItem).filter(WishlistItem.wishlist_id == wishlist_id)
        )
        return len(result.scalars().all())