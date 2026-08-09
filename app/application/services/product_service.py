from uuid import UUID
from typing import List, Optional
from app.infrastructure.database.models import ProductApprovalStatus
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.domain.events import ProductApproved
from app.domain.interfaces.event_bus import EventBus


class ProductService:
    def __init__(self, uow: UnitOfWork, event_bus: EventBus):
        self.uow = uow
        self.event_bus = event_bus

    async def create_product(self, seller_id: UUID, data):
        """
        Create a new product with variants and images.
        The product is created in `pending` status and must be approved by admin.
        """
        # 1. Create the product (no images/variants yet)
        product = await self.uow.products.create(
            seller_id=seller_id,
            category_id=data.category_id,
            brand_id=data.brand_id,
            name=data.name,
            slug=data.slug,
            description=data.description,
            price=data.price,
            discount_price=data.discount_price,
            sku=data.sku,
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            meta_keywords=data.meta_keywords,
            tags=data.tags,
            weight=data.weight,
            dimensions=data.dimensions,
            is_active=False,
            approval_status=ProductApprovalStatus.PENDING
        )

        # 2. ⚠️ CRITICAL: Flush to assign product.id before using it as FK
        await self.uow.session.flush()
        print("PRODUCT OBJECT:", product)
        print("PRODUCT ID:", product.id)

        # 3. Now product.id is available — create variants
        for var_data in data.variants:
            await self.uow.variants.create(
                product_id=product.id,      # Now valid
                sku=var_data.sku,
                price_override=var_data.price_override,
                stock=var_data.stock,
                reserved_stock=0,
                attributes=var_data.attributes
            )

        # 4. Create images — product.id is now valid
        for img_data in data.images:
            image = await self.uow.product_images.create(
                product_id=product.id,      # Now valid
                url=img_data.url,
                is_primary=img_data.is_primary,
                sort_order=img_data.sort_order
            )
            print("IMAGE OBJECT:", image.__dict__)
            print("IMAGE ID:", image.id)

        # 5. Commit everything atomically
        await self.uow.commit()
        await self.uow.refresh(product)
        return product

    async def approve_product(self, product_id: UUID, admin_id: UUID):
        """Approve a product (admin only)."""
        product = await self.uow.products.get(product_id)
        if not product:
            raise BusinessError("Product not found")
        if product.approval_status == ProductApprovalStatus.APPROVED:
            return product

        product.approval_status = ProductApprovalStatus.APPROVED
        product.is_active = True
        await self.uow.commit()

        # Publish event for asynchronous tasks (e.g., indexing, notifications)
        await self.event_bus.publish(
            ProductApproved(product_id=product.id, seller_id=product.seller_id)
        )
        await self.uow.refresh(product)
        return product

    async def reject_product(self, product_id: UUID, admin_id: UUID, reason: Optional[str] = None):
        """Reject a product with optional reason."""
        product = await self.uow.products.get(product_id)
        if not product:
            raise BusinessError("Product not found")
        product.approval_status = ProductApprovalStatus.REJECTED
        product.is_active = False
        # Optionally store rejection reason in a separate field (if exists)
        await self.uow.commit()
        await self.uow.refresh(product)
        return product

    async def get_approved_products(self, skip: int = 0, limit: int = 20):
        """Public method to fetch approved and active products."""
        return await self.uow.products.get_approved_products(skip, limit)

    async def get_product_by_id(self, product_id: UUID):
        """Get a product by ID (with approval/visibility checks)."""
        product = await self.uow.products.get(product_id)
        if not product:
            raise BusinessError("Product not found")
        if product.approval_status != ProductApprovalStatus.APPROVED or not product.is_active:
            raise BusinessError("Product not available")
        return product