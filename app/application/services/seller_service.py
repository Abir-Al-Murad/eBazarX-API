from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.infrastructure.database.models import Seller, SellerStatus, UserRole
from app.api.v1.schemas.seller import SellerApplicationCreate

class SellerService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def apply_seller(self, user_id: UUID, data: SellerApplicationCreate) -> Seller:
        # Check if user already has a seller record
        existing = await self.uow.sellers.get_by_user_id(user_id)
        if existing:
            raise BusinessError("User already applied as seller")

        # Check shop slug uniqueness
        if await self.uow.sellers.get_by_slug(data.shop_slug):
            raise BusinessError("Shop slug already taken")

        # Create seller with pending status
        seller = await self.uow.sellers.create(
            user_id=user_id,
            shop_name=data.shop_name,
            shop_slug=data.shop_slug,
            description=data.description,
            phone=data.phone,
            email=data.email,
            address=data.address,
            city=data.city,
            district=data.district,
            country=data.country,
            trade_license=data.trade_license,
            nid=data.nid,
            tin=data.tin,
            status=SellerStatus.PENDING,
            commission_rate=10.00,
        )
        await self.uow.commit()
        await self.uow.refresh(seller)
        return seller

    async def update_status(
        self,
        seller_id: UUID,
        status: SellerStatus,
        admin_notes: Optional[str] = None
    ) -> Seller:
        seller = await self.uow.sellers.get(seller_id)
        if not seller:
            raise BusinessError("Seller not found")

        # Get the associated user
        user = await self.uow.users.get(seller.user_id)
        if not user:
            raise BusinessError("User not found")

        # Update seller status
        seller.status = status

        # Update user role based on seller status
        if status == SellerStatus.APPROVED:
            user.role = UserRole.SELLER
        elif status in (SellerStatus.REJECTED, SellerStatus.SUSPENDED):
            # Only revert if user was a seller, otherwise keep as customer
            if user.role == UserRole.SELLER:
                user.role = UserRole.CUSTOMER

        # Optionally store admin_notes if you have a field for it
        # You could add a column `admin_notes` to sellers table
        # For now, we'll just update the status

        await self.uow.commit()
        await self.uow.refresh(seller)
        await self.uow.refresh(user)
        return seller

    async def get_pending_sellers(self, skip: int = 0, limit: int = 20) -> Sequence[Seller]:
        return await self.uow.sellers.get_by_status(SellerStatus.PENDING, skip, limit)

    async def get_seller_by_user(self, user_id: UUID) -> Optional[Seller]:
        return await self.uow.sellers.get_by_user_id(user_id)