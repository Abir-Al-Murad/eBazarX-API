from decimal import Decimal
from uuid import UUID
from typing import List, Optional, Dict, Any
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError, InsufficientStockError, InvalidCouponError
from app.infrastructure.database.models import Order, OrderStatus, PaymentStatus


class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def place_order(
        self,
        user_id: UUID,
        address_id: UUID,
        items: List[Dict[str, Any]],  # [{"variant_id": UUID, "quantity": int}]
        coupon_code: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Order:
        # 1. Validate address belongs to user
        address = await self.uow.addresses.get(address_id)
        if not address or address.user_id != user_id:
            raise BusinessError("Invalid address")

        # 2. Validate items and build order item data with price snapshot
        subtotal = Decimal(0)
        order_items_data = []

        for item in items:
            variant = await self.uow.variants.get(item["variant_id"])
            if not variant:
                raise BusinessError(f"Variant {item['variant_id']} not found")
            # Check stock
            available = variant.stock - variant.reserved_stock
            if available < item["quantity"]:
                raise InsufficientStockError(f"Insufficient stock for variant {variant.sku}")

            product = await self.uow.products.get(variant.product_id)
            if not product:
                raise BusinessError(f"Product for variant {variant.id} not found")

            price = variant.price_override or product.price
            subtotal += price * item["quantity"]

            # Reserve stock
            variant.reserved_stock += item["quantity"]

            # Prepare order item data
            product_image = product.images[0].url if product.images and len(product.images) > 0 else None
            size = variant.attributes.get("size") if variant.attributes else None
            color = variant.attributes.get("color") if variant.attributes else None

            order_items_data.append({
                "product_id": product.id,
                "variant_id": variant.id,
                "seller_id": product.seller_id,
                "quantity": item["quantity"],
                "price_at_time": price,
                "product_name_at_time": product.name,
                "product_image_at_time": product_image,
                "size_at_time": size,
                "color_at_time": color,
            })

        # 3. Apply coupon (simplified)
        coupon = None
        discount_amount = Decimal(0)
        if coupon_code:
            coupon = await self.uow.coupons.get_by_code(coupon_code)
            if not coupon or not coupon.is_active:
                raise InvalidCouponError("Invalid or inactive coupon")
            if coupon.discount_type == "percentage":
                discount = subtotal * (coupon.discount_value / 100)
                if coupon.max_discount and discount > coupon.max_discount:
                    discount = coupon.max_discount
                discount_amount = discount
            else:
                discount_amount = coupon.discount_value

        # 4. Compute shipping, tax (stubbed)
        shipping_fee = Decimal(10)  # mock
        tax = Decimal(0)

        grand_total = subtotal - discount_amount + shipping_fee + tax

        # 5. Create order
        order = await self.uow.orders.create(
            user_id=user_id,
            address_id=address_id,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            tax=tax,
            discount_amount=discount_amount,
            grand_total=grand_total,
            payment_method=None,
            payment_status=PaymentStatus.PENDING,
            order_status=OrderStatus.PENDING,
            notes=notes,
            coupon_id=coupon.id if coupon else None
        )

        # ⚠️ CRITICAL: FLUSH the order to get its ID before creating child records
        await self.uow.session.flush()

        # 6. Create order items (order.id is now available)
        for item_data in order_items_data:
            await self.uow.order_items.create(
                order_id=order.id,
                **item_data
            )

        # 7. Clear user's cart (if we have cart module)
        # (We'll clear cart after successful order placement)
        # This could be done asynchronously or here.

        await self.uow.commit()

        # 8. Re-fetch the order with items eager-loaded to avoid MissingGreenlet
        order_with_items = await self.uow.orders.get(order.id)  # Repository uses selectinload
        if not order_with_items:
            raise BusinessError("Failed to retrieve created order")

        return order_with_items