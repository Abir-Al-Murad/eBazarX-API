from sqlalchemy import select, update
from uuid import UUID
from typing import List, Optional
from app.infrastructure.database.models import OrderItem, OrderStatus
from .base import AsyncBaseRepository

class OrderItemRepository(AsyncBaseRepository[OrderItem]):
    async def get_by_seller(self, seller_id: UUID, skip: int = 0, limit: int = 100) -> List[OrderItem]:
        result = await self.session.execute(
            select(OrderItem).filter(OrderItem.seller_id == seller_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_order(self, order_id: UUID) -> List[OrderItem]:
        result = await self.session.execute(select(OrderItem).filter(OrderItem.order_id == order_id))
        return list(result.scalars().all())
    
    async def update_status(self, order_item_id: UUID, status: OrderStatus) -> Optional[OrderItem]:
        stmt = update(OrderItem).where(OrderItem.id == order_item_id).values(status=status).returning(OrderItem)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()