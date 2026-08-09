from sqlalchemy import select, and_
from datetime import datetime
from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.models import FlashSale
from .base import AsyncBaseRepository

class FlashSaleRepository(AsyncBaseRepository[FlashSale]):
    async def get(self, id: UUID) -> Optional[FlashSale]:
        result = await self.session.execute(
            select(FlashSale).filter(FlashSale.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[FlashSale]:
        result = await self.session.execute(
            select(FlashSale).offset(skip).limit(limit).order_by(FlashSale.start_date.desc())
        )
        return result.scalars().all()

    async def get_active_flash_sales(self, current_time: datetime) -> Sequence[FlashSale]:
        result = await self.session.execute(
            select(FlashSale).filter(
                FlashSale.is_active == True,
                FlashSale.start_date <= current_time,
                FlashSale.end_date >= current_time
            )
        )
        return result.scalars().all()