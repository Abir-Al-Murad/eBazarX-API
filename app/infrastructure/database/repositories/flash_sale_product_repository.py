from sqlalchemy import select
from uuid import UUID
from typing import Sequence
from app.infrastructure.database.models import FlashSaleProduct
from .base import AsyncBaseRepository

class FlashSaleProductRepository(AsyncBaseRepository[FlashSaleProduct]):
    async def get_by_flash_sale(self, flash_sale_id: UUID) -> Sequence[FlashSaleProduct]:
        result = await self.session.execute(
            select(FlashSaleProduct).filter(FlashSaleProduct.flash_sale_id == flash_sale_id)
        )
        return result.scalars().all()