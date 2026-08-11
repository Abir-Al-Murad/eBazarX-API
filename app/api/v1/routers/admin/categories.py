from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_admin
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(
    prefix="/admin/categories",
    tags=["Admin Categories"],
    dependencies=[Depends(get_current_admin)]
)

# ============================================================
# GET: List all categories (with pagination & filters)
# ============================================================
@router.get("/", response_model=List[CategoryResponse])
async def list_categories_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    slug: Optional[str] = None,
    parent_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    include_deleted: bool = False,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Admin: List categories with filtering and pagination.
    Can optionally include soft-deleted categories.
    """
    # Build filters
    filters = {}
    if name:
        filters["name"] = name
    if slug:
        filters["slug"] = slug
    if parent_id is not None:
        filters["parent_id"] = parent_id
    if is_active is not None:
        filters["is_active"] = is_active
    filters["include_deleted"] = include_deleted

    categories, total = await uow.categories.get_all_admin(skip, limit, filters)
    return categories

# ============================================================
# GET: Single category by ID
# ============================================================
@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category_admin(
    category_id: UUID,
    include_deleted: bool = False,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Admin: Get a single category by ID.
    Optionally include soft-deleted categories.
    """
    category = await uow.categories.get_admin(category_id, include_deleted)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

# ============================================================
# POST: Create a new category
# ============================================================
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    # Validate parent existence (if provided)
    if data.parent_id:
        parent = await uow.categories.get(data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=404,
                detail=f"Parent category with id {data.parent_id} not found"
            )

    # Check duplicate slug
    if await uow.categories.check_slug_exists(data.slug):
        raise HTTPException(
            status_code=409,
            detail=f"Category with slug '{data.slug}' already exists"
        )

    category = await uow.categories.create(
        name=data.name,
        slug=data.slug,
        description=data.description,
        image_url=data.image_url,
        parent_id=data.parent_id,
        is_active=True
    )
    await uow.commit()
    await uow.refresh(category)
    return category

# ============================================================
# PUT: Update an existing category
# ============================================================
@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    category = await uow.categories.get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Validate parent (if updating)
    if data.parent_id is not None:
        if data.parent_id == category_id:
            raise HTTPException(
                status_code=400,
                detail="Category cannot be its own parent"
            )
        parent = await uow.categories.get(data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=404,
                detail=f"Parent category with id {data.parent_id} not found"
            )

    # Check slug uniqueness (if slug is being changed)
    if data.slug is not None:
        if await uow.categories.check_slug_exists(data.slug, exclude_id=category_id):
            raise HTTPException(
                status_code=409,
                detail=f"Category with slug '{data.slug}' already exists"
            )

    # Apply updates
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    await uow.commit()
    await uow.refresh(category)
    return category

# ============================================================
# DELETE: Soft-delete a category
# ============================================================
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    category = await uow.categories.get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Soft delete
    category.deleted_at = datetime.now(timezone.utc)
    await uow.commit()
    return None  # 204 No Content