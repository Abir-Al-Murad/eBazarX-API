from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from typing import Optional, Dict, Any
import httpx
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.infrastructure.database.models import OrderStatus, Payment, PaymentStatus, PaymentGateway, Order
from app.core.config import settings

class PaymentService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_pass = settings.SSLCOMMERZ_STORE_PASS.get_secret_value()
        self.sandbox = settings.SSLCOMMERZ_SANDBOX_MODE

        # SSLCommerz API endpoints
        if self.sandbox:
            self.init_url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
            self.validation_url = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
        else:
            self.init_url = "https://secure.sslcommerz.com/gwprocess/v4/api.php"
            self.validation_url = "https://secure.sslcommerz.com/validator/api/validationserverAPI.php"

    async def initiate_payment(
        self,
        order_id: UUID,
        success_url: str,
        cancel_url: str,
        gateway: PaymentGateway = PaymentGateway.SSLCOMMERZ,
    ) -> Dict[str, Any]:
        """
        Initiate SSLCommerz payment session.
        Returns redirect_url and transaction_id.
        """
        order = await self.uow.orders.get(order_id)
        if not order:
            raise BusinessError("Order not found")

        # Create a Payment record in pending state
        payment = await self.uow.payments.create(
            order_id=order_id,
            gateway=gateway,
            amount=order.grand_total,
            currency="BDT",
            status=PaymentStatus.PENDING,
        )
        await self.uow.session.flush()   # get payment.id

        # Prepare SSLCommerz post data
        post_data = {
            "store_id": self.store_id,
            "store_passwd": self.store_pass,
            "total_amount": str(order.grand_total),
            "currency": "BDT",
            "tran_id": f"EBZ-{order_id.hex[:8]}-{payment.id.hex[:4]}",
            "success_url": f"{success_url}?payment_id={payment.id}&order_id={order_id}",
            "fail_url": f"{cancel_url}?payment_id={payment.id}&order_id={order_id}",
            "cancel_url": f"{cancel_url}?payment_id={payment.id}&order_id={order_id}",
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
            # Mark payment as failed
            payment.status = PaymentStatus.FAILED
            await self.uow.commit()
            raise BusinessError(f"SSLCommerz initiation failed: {result.get('failedreason', 'Unknown error')}")

        # Save transaction ID (SSLCommerz session key)
        payment.transaction_id = result.get("sessionkey") or result.get("tran_id")
        payment.gateway_response = result
        await self.uow.commit()
        await self.uow.refresh(payment)

        return {
            "payment_id": payment.id,
            "order_id": order_id,
            "gateway": gateway.value,
            "redirect_url": result.get("GatewayPageURL"),
            "transaction_id": payment.transaction_id,
        }

    async def handle_webhook(self, payload: Dict[str, Any]) -> Payment:
        """
        Handle SSLCommerz success/fail/cancel callback (webhook or redirect).
        """
        val_id = payload.get("val_id")
        tran_id = payload.get("tran_id")
        status = payload.get("status")   # "VALID" or "FAILED"
        amount = Decimal(payload.get("amount", 0))

        if not val_id or not tran_id:
            raise BusinessError("Missing validation parameters")

        payment = await self.uow.payments.get_by_transaction_id(tran_id)
        if not payment:
            raise BusinessError("Payment not found")

        # Verify payment with SSLCommerz validation API
        async with httpx.AsyncClient() as client:
            validation_params = {
                "val_id": val_id,
                "store_id": self.store_id,
                "store_passwd": self.store_pass,
                "format": "json",
            }
            resp = await client.get(self.validation_url, params=validation_params)
            validation_data = resp.json()

        if validation_data.get("status") != "VALID":
            payment.status = PaymentStatus.FAILED
            payment.gateway_response = validation_data
            await self.uow.commit()
            return payment

        # Verify amount
        if Decimal(validation_data.get("amount", 0)) != payment.amount:
            payment.status = PaymentStatus.FAILED
            payment.gateway_response = validation_data
            await self.uow.commit()
            raise BusinessError("Amount mismatch")

        # Payment is valid
        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.now(timezone.utc)
        payment.gateway_response = validation_data
        await self.uow.commit()
        await self.uow.refresh(payment)

        # Update order status
        order = await self.uow.orders.get(payment.order_id)
        if order:
            order.payment_status = PaymentStatus.PAID
            order.order_status = OrderStatus.PROCESSING
            await self.uow.commit()

        return payment

    async def get_payment_status(self, payment_id: UUID) -> Payment:
        payment = await self.uow.payments.get(payment_id)
        if not payment:
            raise BusinessError("Payment not found")
        return payment