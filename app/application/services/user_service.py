from uuid import UUID
from typing import Optional
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.infrastructure.database.models import User, UserRole

class UserService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_public_profile(self, user_id: UUID) -> Optional[User]:
        """Public profile (basic info, no sensitive fields)."""
        user = await self.uow.users.get_public_profile(user_id)
        if not user:
            raise BusinessError("User not found")
        return user

    async def get_authenticated_profile(self, user_id: UUID) -> dict:
        """
        Full profile for the authenticated user.
        Returns a dict with nested shop or admin objects.
        """
        user = await self.uow.users.get_with_seller(user_id)
        if not user:
            raise BusinessError("User not found")

        # Base common fields
        response = {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "profile_image": user.profile_image,
            "role": user.role,
            "is_verified": user.is_verified,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        # Role‑specific additions
        if user.role == UserRole.SELLER and user.seller:
            seller = user.seller
            response["shop"] = {
                "id": seller.id,
                "shop_name": seller.shop_name,
                "shop_slug": seller.shop_slug,
                "logo": seller.logo,
                "cover_image": seller.cover_image,
                "shop_description": seller.description,
                "average_rating": seller.average_rating or 0.0,
                "total_products": seller.total_products or 0,
                "total_followers": 0,
                "verification_status": "verified" if seller.status == "approved" else "pending",
                "is_active": True,
            }
        elif user.role == UserRole.ADMIN:
            response["admin"] = {
                "permissions": [
                    "users.read", "users.write", "products.manage",
                    "orders.manage", "reviews.manage", "shops.manage"
                ],
                "last_login": user.last_login,
                "super_admin": True,
            }

        return response