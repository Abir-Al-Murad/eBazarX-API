from sqlalchemy import select, func
from uuid import UUID
from typing import Optional
from app.infrastructure.database.models import ProductStatistics
from .base import AsyncBaseRepository

class ProductStatisticsRepository(AsyncBaseRepository[ProductStatistics]):
    async def get_by_product(self, product_id: UUID) -> Optional[ProductStatistics]:
        result = await self.session.execute(
            select(ProductStatistics).filter(ProductStatistics.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(self, product_id: UUID, **kwargs) -> ProductStatistics:
        existing = await self.get_by_product(product_id)
        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            stats = await self.create(product_id=product_id, **kwargs)
            await self.session.commit()
            await self.session.refresh(stats)
            return stats