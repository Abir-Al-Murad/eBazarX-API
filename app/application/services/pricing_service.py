from decimal import Decimal
from app.infrastructure.database.models import Coupon
from app.core.exceptions import InvalidCouponError

class PricingService:
    async def apply_coupon(self, coupon: Coupon, subtotal: Decimal) -> Decimal:
        if subtotal < coupon.min_order_amount:  # type: ignore
            raise InvalidCouponError(f"Minimum order amount {coupon.min_order_amount} required")
        if coupon.discount_type == "percentage":
            discount = subtotal * (coupon.discount_value / 100)
            if coupon.max_discount and discount > coupon.max_discount:
                discount = coupon.max_discount
        else:  # fixed
            discount = coupon.discount_value
        return discount