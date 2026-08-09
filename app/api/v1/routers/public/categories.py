from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.api.v1.dependencies.auth import get_uow
from app.infrastructure.database.unit_of_work import UnitOfWork

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: Optional[str]
    image_url: Optional[str]
    parent_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =====================================================
# Root Categories
# =====================================================

@router.get("/", response_model=List[CategoryResponse])
async def list_root_categories(
    skip: int = 0,
    limit: int = 100,
    uow: UnitOfWork = Depends(get_uow),
):
    return await uow.categories.get_root_categories(
        skip=skip,
        limit=limit,
    )


# =====================================================
# Single Category
# =====================================================

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
):
    category = await uow.categories.get(category_id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


# =====================================================
# Child Categories
# =====================================================

@router.get(
    "/{category_id}/children",
    response_model=List[CategoryResponse],
)
async def get_child_categories(
    category_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
):
    parent = await uow.categories.get(category_id)

    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent category not found",
        )

    return await uow.categories.get_children(category_id)