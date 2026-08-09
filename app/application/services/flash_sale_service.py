from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, List
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.api.v1.schemas.flash_sale import FlashSaleCreate, FlashSaleUpdate

class FlashSaleService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_flash_sale(self, data: FlashSaleCreate):
        if data.start_date >= data.end_date:
            raise BusinessError("Start date must be before end date")

        # Validate products
        for product_data in data.products:
            product = await self.uow.products.get(product_data.product_id)
            if not product:
                raise BusinessError(f"Product {product_data.product_id} not found")
            # Check if product already in another active flash sale
            # (optional check)

        flash_sale = await self.uow.flash_sales.create(
            name=data.name,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            is_active=data.is_active
        )

        for product_data in data.products:
            await self.uow.flash_sale_products.create(
                flash_sale_id=flash_sale.id,
                product_id=product_data.product_id,
                discount_price=product_data.discount_price,
                stock_limit=product_data.stock_limit,
                sold=0
            )

        await self.uow.commit()
        await self.uow.refresh(flash_sale)
        return flash_sale

    async def update_flash_sale(self, flash_sale_id: UUID, data: FlashSaleUpdate):
        flash_sale = await self.uow.flash_sales.get(flash_sale_id)
        if not flash_sale:
            raise BusinessError("Flash sale not found")

        if data.start_date and data.end_date and data.start_date >= data.end_date:
            raise BusinessError("Start date must be before end date")

        update_data = data.model_dump(exclude_unset=True, exclude={'products'})
        for key, value in update_data.items():
            setattr(flash_sale, key, value)

        # Update products if provided
        if data.products is not None:
            # Remove existing products
            existing_products = await self.uow.flash_sale_products.get_by_flash_sale(flash_sale_id)
            for existing in existing_products:
                await self.uow.flash_sale_products.delete(existing.id)

            # Add new products
            for product_data in data.products:
                product = await self.uow.products.get(product_data.product_id)
                if not product:
                    raise BusinessError(f"Product {product_data.product_id} not found")
                await self.uow.flash_sale_products.create(
                    flash_sale_id=flash_sale_id,
                    product_id=product_data.product_id,
                    discount_price=product_data.discount_price,
                    stock_limit=product_data.stock_limit,
                    sold=0
                )

        await self.uow.commit()
        await self.uow.refresh(flash_sale)
        return flash_sale

    async def delete_flash_sale(self, flash_sale_id: UUID):
        flash_sale = await self.uow.flash_sales.get(flash_sale_id)
        if not flash_sale:
            raise BusinessError("Flash sale not found")
        await self.uow.flash_sales.delete(flash_sale_id)
        await self.uow.commit()