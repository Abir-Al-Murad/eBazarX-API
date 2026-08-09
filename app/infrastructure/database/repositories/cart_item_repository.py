from sqlalchemy import  delete, select
from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.models import CartItem
from .base import AsyncBaseRepository

class CartItemRepository(AsyncBaseRepository[CartItem]):
    async def get_by_cart_and_variant(self, cart_id: UUID, variant_id: UUID) -> Optional[CartItem]:
        result = await self.session.execute(
            select(CartItem).filter(CartItem.cart_id == cart_id, CartItem.variant_id == variant_id)
        )
        return result.scalar_one_or_none()
    
    async def delete_by_cart(self, cart_id: UUID) -> None:
        await self.session.execute(delete(CartItem).filter(CartItem.cart_id == cart_id))
        
    async def get_by_cart(self, cart_id: UUID) -> Sequence[CartItem]:
        result = await self.session.execute(
            select(CartItem).filter(CartItem.cart_id == cart_id)
        )
        return result.scalars().all()
