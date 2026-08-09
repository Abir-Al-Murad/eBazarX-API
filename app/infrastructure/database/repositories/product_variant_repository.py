from sqlalchemy import select
from uuid import UUID
from typing import List, Optional, Sequence
from app.infrastructure.database.models import ProductVariant
from .base import AsyncBaseRepository

class ProductVariantRepository(AsyncBaseRepository[ProductVariant]):
    async def get_by_product(self, product_id: UUID) -> List[ProductVariant]:
        result = await self.session.execute(select(ProductVariant).filter(ProductVariant.product_id == product_id))
        return result.scalars().all() # type: ignore
    
    async def get_by_sku(self, sku: str) -> Optional[ProductVariant]:
        result = await self.session.execute(select(ProductVariant).filter(ProductVariant.sku == sku))
        return result.scalar_one_or_none()
    
    async def get_by_ids(self, ids: List[UUID]) -> Sequence[ProductVariant]:
        if not ids:
            return []
        result = await self.session.execute(
            select(ProductVariant).filter(ProductVariant.id.in_(ids))
        )
        return result.scalars().all()