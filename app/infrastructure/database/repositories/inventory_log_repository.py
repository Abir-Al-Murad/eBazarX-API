from sqlalchemy import select
from uuid import UUID
from typing import List
from app.infrastructure.database.models import InventoryLog
from .base import AsyncBaseRepository

class InventoryLogRepository(AsyncBaseRepository[InventoryLog]):
    async def get_by_order(self, order_id: UUID) -> List[InventoryLog]:
        result = await self.session.execute(
            select(InventoryLog).filter(InventoryLog.order_id == order_id)
        )
        return result.scalars().all() # type: ignore
    
    async def get_by_variant(self, variant_id: UUID) -> List[InventoryLog]:
        result = await self.session.execute(
            select(InventoryLog).filter(InventoryLog.variant_id == variant_id)
        )
        return result.scalars().all() # type: ignore