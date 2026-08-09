from sqlalchemy import select
from uuid import UUID
from typing import Sequence
from app.infrastructure.database.models import ProductImage
from .base import AsyncBaseRepository

class ProductImageRepository(AsyncBaseRepository[ProductImage]):
    async def get_by_product(self, product_id: UUID) -> Sequence[ProductImage]:
        result = await self.session.execute(
            select(ProductImage).filter(ProductImage.product_id == product_id)
        )
        return result.scalars().all()