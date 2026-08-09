from fastapi import APIRouter, Depends, HTTPException, status
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

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    # Validate parent existence (if provided)
    if data.parent_id:
        parent = await uow.categories.get_parent(data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with id {data.parent_id} not found"
            )

    # Check duplicate slug
    if await uow.categories.check_slug_exists(data.slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
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

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    category = await uow.categories.get(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Validate parent (if updating)
    if data.parent_id is not None:
        if data.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent"
            )
        parent = await uow.categories.get_parent(data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with id {data.parent_id} not found"
            )

    # Check slug uniqueness (if slug is being changed)
    if data.slug is not None:
        if await uow.categories.check_slug_exists(data.slug, exclude_id=category_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with slug '{data.slug}' already exists"
            )

    # Apply updates
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    await uow.commit()
    await uow.refresh(category)
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    uow: UnitOfWork = Depends(get_uow)
):
    category = await uow.categories.get(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Check if category has children (optional: prevent deletion if children exist)
    # We could add a method in repository, but we'll keep it simple – soft delete only.
    category.deleted_at = datetime.now(timezone.utc)
    await uow.commit()
    return None  # 204 No Content