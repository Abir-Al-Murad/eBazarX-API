from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List
from app.api.v1.schemas.coupon import CouponCreate, CouponUpdate
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError, InvalidCouponError
from app.infrastructure.database.models import Coupon, DiscountType

class CouponService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def validate_coupon(self, code: str, subtotal: Decimal, user_id: UUID):
        coupon = await self.uow.coupons.get_by_code(code)
        if not coupon:
            return {"valid": False, "message": "Coupon not found"}

        # Check if active
        if not coupon.is_active:
            return {"valid": False, "message": "Coupon is inactive"}

        now = datetime.now(timezone.utc)
        if not (coupon.start_date <= now <= coupon.end_date):
            return {"valid": False, "message": "Coupon is not valid for current date"}

        # Check min order amount
        if coupon.min_order_amount and subtotal < coupon.min_order_amount:
            return {
                "valid": False,
                "message": f"Minimum order amount {coupon.min_order_amount} required"
            }

        # Check usage limit
        used_count = await self.uow.coupons.get_usage_count(coupon.id)
        if coupon.usage_limit and used_count >= coupon.usage_limit:
            return {"valid": False, "message": "Coupon usage limit exceeded"}

        # Check per-user limit
        user_used = await self.uow.coupons.get_user_usage_count(coupon.id, user_id)
        if coupon.per_user_limit and user_used >= coupon.per_user_limit:
            return {"valid": False, "message": "You have already used this coupon"}

        # Calculate discount
        discount_amount = Decimal(0)
        if coupon.discount_type == DiscountType.PERCENTAGE:
            discount = subtotal * (coupon.discount_value / 100)
            if coupon.max_discount and discount > coupon.max_discount:
                discount = coupon.max_discount
            discount_amount = discount
        else:  # fixed
            discount_amount = coupon.discount_value

        # Optionally, ensure discount doesn't exceed subtotal
        if discount_amount > subtotal:
            discount_amount = subtotal

        return {
            "valid": True,
            "discount_amount": discount_amount,
            "coupon_id": coupon.id,
            "message": "Coupon is valid"
        }

    async def create_coupon(
        self,
        seller_id: Optional[UUID],
        data: CouponCreate,
        product_ids: Optional[List[UUID]] = None,
        category_ids: Optional[List[UUID]] = None
    ):
        # Check code uniqueness
        existing = await self.uow.coupons.get_by_code(data.code)
        if existing:
            raise BusinessError(f"Coupon with code '{data.code}' already exists")

        # Validate dates
        if data.start_date >= data.end_date:
            raise BusinessError("Start date must be before end date")

        # Create coupon
        coupon = await self.uow.coupons.create(
            seller_id=seller_id,
            code=data.code,
            description=data.description,
            discount_type=data.discount_type,
            discount_value=data.discount_value,
            min_order_amount=data.min_order_amount,
            max_discount=data.max_discount,
            usage_limit=data.usage_limit,
            per_user_limit=data.per_user_limit,
            is_active=data.is_active,
            start_date=data.start_date,
            end_date=data.end_date
        )

        # Link products if provided
        if product_ids:
            for pid in product_ids:
                product = await self.uow.products.get(pid)
                if product:
                    await self.uow.coupon_products.create(
                        coupon_id=coupon.id,
                        product_id=pid
                    )

        # Link categories if provided
        if category_ids:
            for cid in category_ids:
                category = await self.uow.categories.get(cid)
                if category:
                    await self.uow.coupon_categories.create(
                        coupon_id=coupon.id,
                        category_id=cid
                    )

        await self.uow.commit()
        await self.uow.refresh(coupon)
        return coupon

    async def update_coupon(self, coupon_id: UUID, data: CouponUpdate):
        coupon = await self.uow.coupons.get(coupon_id)
        if not coupon:
            raise BusinessError("Coupon not found")

        # If code changed, ensure uniqueness
        if data.code and data.code != coupon.code:
            existing = await self.uow.coupons.get_by_code(data.code)
            if existing and existing.id != coupon_id:
                raise BusinessError(f"Coupon with code '{data.code}' already exists")

        update_data = data.model_dump(exclude_unset=True, exclude={'product_ids', 'category_ids'})
        for key, value in update_data.items():
            setattr(coupon, key, value)

        # Handle product/category associations if provided
        if data.product_ids is not None:
            # Clear existing and add new
            await self.uow.coupon_products.delete_by_coupon(coupon.id)
            for pid in data.product_ids:
                product = await self.uow.products.get(pid)
                if product:
                    await self.uow.coupon_products.create(
                        coupon_id=coupon.id,
                        product_id=pid
                    )

        if data.category_ids is not None:
            await self.uow.coupon_categories.delete_by_coupon(coupon.id)
            for cid in data.category_ids:
                category = await self.uow.categories.get(cid)
                if category:
                    await self.uow.coupon_categories.create(
                        coupon_id=coupon.id,
                        category_id=cid
                    )

        await self.uow.commit()
        await self.uow.refresh(coupon)
        return coupon

    async def delete_coupon(self, coupon_id: UUID):
        coupon = await self.uow.coupons.get(coupon_id)
        if not coupon:
            raise BusinessError("Coupon not found")
        # Soft delete or hard delete? We'll soft delete by setting is_active=False
        coupon.is_active = False
        await self.uow.commit()

    async def get_coupon_with_usage(self, coupon_id: UUID):
        coupon = await self.uow.coupons.get(coupon_id)
        if not coupon:
            raise BusinessError("Coupon not found")
        used_count = await self.uow.coupons.get_usage_count(coupon_id)
        return {"coupon": coupon, "used_count": used_count}