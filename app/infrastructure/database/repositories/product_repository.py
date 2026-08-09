from ast import stmt
from unittest import skip

from sqlalchemy import func, select, or_
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.models import Product, ProductApprovalStatus
from .base import AsyncBaseRepository

class ProductRepository(AsyncBaseRepository[Product]):

    async def get(self, id: UUID) -> Optional[Product]:
        stmt = (
            select(Product)
            .filter(Product.id == id, Product.deleted_at.is_(None))
            .options(
                selectinload(Product.variants),
                selectinload(Product.images),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[UUID] = None,
        seller_id: Optional[UUID] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True,
        approval_status: Optional[ProductApprovalStatus] = None
    ) -> Sequence[Product]:
        stmt = select(Product).filter(Product.deleted_at.is_(None))
        print("DEBUG: get_all called with parameters:")
        print(stmt)
        if is_active is not None:
            stmt = stmt.filter(Product.is_active == is_active)
        if category_id:
            stmt = stmt.filter(Product.category_id == category_id)
        if seller_id:
            stmt = stmt.filter(Product.seller_id == seller_id)
        if approval_status:
            stmt = stmt.filter(Product.approval_status == approval_status)
        if search:
            stmt = stmt.filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                    Product.slug.ilike(f"%{search}%")
                )
            )
        stmt = (
            stmt
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Product.variants),
                selectinload(Product.images),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_by_seller(self, seller_id: UUID, skip: int = 0, limit: int = 100) -> Sequence[Product]:
        # Reuse get_all with seller filter
        return await self.get_all(skip=skip, limit=limit, seller_id=seller_id)

    async def get_by_slug(self, slug: str) -> Optional[Product]:
        stmt = (
            select(Product)
            .filter(Product.slug == slug, Product.deleted_at.is_(None))
            .options(
                selectinload(Product.variants),
                selectinload(Product.images),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_products(
        self,
        skip: int = 0,
        limit: int = 20
        ) -> Sequence[Product]:

        stmt = (
            select(Product)
            .where(
            Product.deleted_at.is_(None),
            Product.approval_status == ProductApprovalStatus.PENDING
        )
        .options(
            selectinload(Product.variants),
            selectinload(Product.images),
        )
        .offset(skip)
        .limit(limit)
        )

        result = await self.session.execute(stmt)

        return result.scalars().unique().all()

    async def get_approved_products(self, skip: int = 0, limit: int = 20) -> Sequence[Product]:
        stmt = (
            select(Product)
            .filter(
                Product.approval_status == ProductApprovalStatus.APPROVED,
                Product.is_active == True,
                Product.deleted_at.is_(None)
            )
            .offset(skip)
            .limit(limit)
            .order_by(Product.created_at.desc())
            .options(
                selectinload(Product.variants),
                selectinload(Product.images),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def update_approval(self, product_id: UUID, status: ProductApprovalStatus) -> Optional[Product]:
        product = await self.get(product_id)
        if product:
            product.approval_status = status
            await self.session.commit()
            await self.session.refresh(product)
        return product

    async def count_all(self) -> int:
        result = await self.session.execute(
            select(func.count()).filter(Product.deleted_at.is_(None))
        )
        return result.scalar() or 0

    async def count_by_approval_status(self, status: ProductApprovalStatus) -> int:
        result = await self.session.execute(
            select(func.count()).filter(Product.approval_status == status, Product.deleted_at.is_(None))
        )
        return result.scalar() or 0

    async def count_by_seller(self, seller_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).filter(Product.seller_id == seller_id, Product.deleted_at.is_(None))
        )
        return result.scalar() or 0

    async def count_approved_products(self) -> int:
        stmt = (
            select(func.count())
            .filter(
                Product.approval_status == ProductApprovalStatus.APPROVED,
                Product.is_active == True,
                Product.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    # Optional: use this for single product retrieval if you want to separate from get()
    async def get_with_details(self, product_id: UUID) -> Optional[Product]:
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.variants),
                selectinload(Product.images),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()