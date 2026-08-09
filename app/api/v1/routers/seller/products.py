from itertools import product

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_seller
from app.infrastructure.database.models import Seller, ProductApprovalStatus
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from datetime import datetime, timezone

router = APIRouter(
    prefix="/seller/products",
    tags=["Seller Products"],
    dependencies=[Depends(get_current_seller)]
)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    # Check category exists
    category = await uow.categories.get(data.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check brand if provided
    if data.brand_id:
        brand = await uow.brands.get(data.brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")

    # Check slug uniqueness
    if await uow.products.get_by_slug(data.slug):
        raise HTTPException(status_code=409, detail="Product slug already exists")

    # Check SKU uniqueness globally (or per product? We'll keep unique globally)
    if await uow.variants.get_by_sku(data.sku):
        raise HTTPException(status_code=409, detail="Product SKU already exists")

    # Create product
    product = await uow.products.create(
        seller_id=current_seller.id,
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
        is_active=False,  # Requires admin approval
        approval_status=ProductApprovalStatus.PENDING
    )
    await uow.session.flush()
    print("PRODUCT OBJECT:", product)
    print("PRODUCT ID:", product.id)
    # Create variants
    for v_data in data.variants:
        # Optionally validate attributes against defined attributes? We'll skip for now.
        variant = await uow.variants.create(
            product_id=product.id,
            sku=v_data.sku,
            price_override=v_data.price_override,
            stock=v_data.stock,
            attributes=v_data.attributes
        )
        # Check if SKU is unique across all variants
        # Already checked product SKU, but variant SKU should be unique too.
        # We'll enforce via DB unique constraint.

    # Create images
    for img_data in data.images:
        await uow.product_images.create(
            product_id=product.id,
            url=img_data.url,
            is_primary=img_data.is_primary,
            sort_order=img_data.sort_order
        )

    await uow.commit()

    product = await uow.products.get_with_details(product.id)

    return product

@router.get("/", response_model=List[ProductResponse])
async def list_my_products(
    skip: int = 0,
    limit: int = 20,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    products = await uow.products.get_by_seller(current_seller.id, skip, limit)
    return products

@router.get("/{product_id}", response_model=ProductResponse)
async def get_my_product(
    product_id: UUID,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    product = await uow.products.get(product_id)
    if not product or product.seller_id != current_seller.id:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    product = await uow.products.get(product_id)
    if not product or product.seller_id != current_seller.id:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validation: category, brand, slug, sku if changed.
    if data.category_id is not None:
        category = await uow.categories.get(data.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    if data.brand_id is not None:
        brand = await uow.brands.get(data.brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")

    if data.slug is not None:
        existing = await uow.products.get_by_slug(data.slug)
        if existing and existing.id != product_id:
            raise HTTPException(status_code=409, detail="Slug already used")

    # Update product fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    # If product was previously approved, reset approval to pending to require re-approval?
    # We'll keep the current approval status, but admin can decide.

    await uow.commit()
    await uow.refresh(product)
    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    product = await uow.products.get(product_id)
    if not product or product.seller_id != current_seller.id:
        raise HTTPException(status_code=404, detail="Product not found")
    # Soft delete
    product.deleted_at = datetime.now(timezone.utc)
    await uow.commit()
    return None