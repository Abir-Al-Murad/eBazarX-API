from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.api.v1.schemas.banner import BannerCreate, BannerUpdate

class BannerService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_banner(self, data: BannerCreate):
        # Validate product if provided
        if data.product_id:
            product = await self.uow.products.get(data.product_id)
            if not product:
                raise BusinessError("Product not found")
        # Validate category if provided
        if data.category_id:
            category = await self.uow.categories.get(data.category_id)
            if not category:
                raise BusinessError("Category not found")

        banner = await self.uow.banners.create(
            title=data.title,
            description=data.description,
            image_url=data.image_url,
            link_url=data.link_url,
            product_id=data.product_id,
            category_id=data.category_id,
            position=data.position,
            is_active=data.is_active,
            start_date=data.start_date,
            end_date=data.end_date
        )
        await self.uow.commit()
        await self.uow.refresh(banner)
        return banner

    async def update_banner(self, banner_id: UUID, data: BannerUpdate):
        banner = await self.uow.banners.get(banner_id)
        if not banner:
            raise BusinessError("Banner not found")

        if data.product_id is not None:
            if data.product_id:
                product = await self.uow.products.get(data.product_id)
                if not product:
                    raise BusinessError("Product not found")
            banner.product_id = data.product_id

        if data.category_id is not None:
            if data.category_id:
                category = await self.uow.categories.get(data.category_id)
                if not category:
                    raise BusinessError("Category not found")
            banner.category_id = data.category_id

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key not in ['product_id', 'category_id']:
                setattr(banner, key, value)

        await self.uow.commit()
        await self.uow.refresh(banner)
        return banner

    async def delete_banner(self, banner_id: UUID):
        banner = await self.uow.banners.get(banner_id)
        if not banner:
            raise BusinessError("Banner not found")
        await self.uow.banners.delete(banner_id)
        await self.uow.commit()