from sqlalchemy import select, delete
from uuid import UUID
from typing import List, Optional
from app.infrastructure.database.models import Cart, CartItem
from .base import AsyncBaseRepository

class CartRepository(AsyncBaseRepository[Cart]):
    async def get_by_user(self, user_id: UUID) -> Optional[Cart]:
        result = await self.session.execute(select(Cart).filter(Cart.user_id == user_id))
        return result.scalar_one_or_none()
    
    async def clear_cart(self, cart_id: UUID) -> None:
        await self.session.execute(delete(CartItem).filter(CartItem.cart_id == cart_id))

