from fastapi import Depends, HTTPException, status
from app.infrastructure.database.models import SellerStatus, User, UserRole, Seller
from app.api.v1.dependencies.auth import get_current_user
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.dependencies.auth import get_uow
from uuid import UUID

async def get_current_customer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="Customer only")
    return current_user

async def get_current_seller(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
) -> Seller:
    if current_user.role not in (UserRole.SELLER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Seller or Admin required")
    seller = await uow.sellers.get_by_user_id(current_user.id)
    if not seller:
        raise HTTPException(status_code=403, detail="Not a seller")
    if seller.status != SellerStatus.APPROVED:
        raise HTTPException(status_code=403, detail="Seller not approved")
    return seller

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user