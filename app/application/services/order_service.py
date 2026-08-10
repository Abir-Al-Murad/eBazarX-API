from decimal import Decimal
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import httpx
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError, InsufficientStockError, InvalidCouponError
from app.infrastructure.database.models import Order, OrderStatus, PaymentGateway, PaymentStatus, Payment
from app.core.config import settings
from app.api.v1.schemas.order import OrderPlaceResponse, OrderResponse


class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        # SSLCommerz config
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_pass = settings.SSLCOMMERZ_STORE_PASS.get_secret_value()
        self.sandbox = settings.SSLCOMMERZ_SANDBOX_MODE

        if self.sandbox:
            self.init_url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
            self.validation_url = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
        else:
            self.init_url = "https://secure.sslcommerz.com/gwprocess/v4/api.php"
            self.validation_url = "https://secure.sslcommerz.com/validator/api/validationserverAPI.php"

    async def place_order(
        self,
        user_id: UUID,
        address_id: UUID,
        items: List[Dict[str, Any]],
        payment_method: str = "cod",
        coupon_code: Optional[str] = None,
        notes: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> OrderPlaceResponse:
        """
        Place an order.
        Returns:
            For COD: OrderPlaceResponse with redirect_url=None, payment_id=None
            For SSLCommerz: OrderPlaceResponse with redirect_url and payment_id
        """
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
            available = variant.stock - variant.reserved_stock
            if available < item["quantity"]:
                raise InsufficientStockError(f"Insufficient stock for variant {variant.sku}")

            product = await self.uow.products.get(variant.product_id)
            if not product:
                raise BusinessError(f"Product for variant {variant.id} not found")

            price = variant.price_override or product.price
            subtotal += price * item["quantity"]

            variant.reserved_stock += item["quantity"]

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

        # 3. Apply coupon
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
        shipping_fee = Decimal(10)
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
            payment_method=payment_method,
            payment_status=PaymentStatus.PENDING,
            order_status=OrderStatus.PENDING,
            notes=notes,
            coupon_id=coupon.id if coupon else None,
            payment_intent_id=None,  # will store SSLCommerz transaction ID later
        )

        # Flush to get order ID
        await self.uow.session.flush()

        # 6. Create order items
        for item_data in order_items_data:
            await self.uow.order_items.create(
                order_id=order.id,
                **item_data
            )

        # 7. If SSLCommerz, create Payment record and initiate payment
        redirect_url = None
        payment_id = None
        if payment_method == "sslcommerz":
            if not success_url or not cancel_url:
                raise BusinessError("success_url and cancel_url are required for SSLCommerz")

            # Create Payment record
            payment = await self.uow.payments.create(
                order_id=order.id,
                gateway=PaymentGateway.SSLCOMMERZ,
                amount=grand_total,
                currency="BDT",
                status=PaymentStatus.PENDING,
            )
            await self.uow.session.flush()  # get payment.id

            # Prepare SSLCommerz post data
            post_data = {
                "store_id": self.store_id,
                "store_passwd": self.store_pass,
                "total_amount": str(grand_total),
                "currency": "BDT",
                "tran_id": f"EBZ-{order.id.hex[:8]}-{payment.id.hex[:4]}",
                "success_url": f"{success_url}?payment_id={payment.id}&order_id={order.id}",
                "fail_url": f"{cancel_url}?payment_id={payment.id}&order_id={order.id}",
                "cancel_url": f"{cancel_url}?payment_id={payment.id}&order_id={order.id}",
                "emi_option": 0,
                "cus_name": "Customer",
                "cus_email": "customer@example.com",
                "cus_phone": "01700000000",
                "cus_add1": "Dhaka",
                "cus_city": "Dhaka",
                "cus_country": "Bangladesh",
                "shipping_method": "NO",
                "product_name": "Order Items",
                "product_category": "E-Commerce",
                "product_profile": "general",
            }

            # Send request to SSLCommerz
            async with httpx.AsyncClient() as client:
                response = await client.post(self.init_url, data=post_data)
                result = response.json()

            if result.get("status") != "SUCCESS":
                payment.status = PaymentStatus.FAILED
                await self.uow.commit()
                raise BusinessError(f"SSLCommerz initiation failed: {result.get('failedreason', 'Unknown error')}")

            # Save transaction ID (SSLCommerz session key)
            payment.transaction_id = result.get("sessionkey") or result.get("tran_id")
            payment.gateway_response = result
            await self.uow.commit()
            await self.uow.refresh(payment)

            redirect_url = result.get("GatewayPageURL")
            payment_id = payment.id

        # 8. Commit
        await self.uow.commit()

        # 9. Re-fetch order with items eager-loaded
        order_with_items = await self.uow.orders.get_with_items(order.id)
        if not order_with_items:
            raise BusinessError("Failed to retrieve created order")

        # Convert to Pydantic response model
        order_response = OrderResponse.model_validate(order_with_items)

        # 10. Return response
        return OrderPlaceResponse(
            order=order_response,
            redirect_url=redirect_url,
            payment_id=str(payment_id) if payment_id else None,
        )