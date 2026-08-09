from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.infrastructure.database.models import PaymentStatus, PaymentGateway, OrderStatus

class PaymentService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def initiate_payment(
        self,
        order_id: UUID,
        gateway: PaymentGateway,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ):
        # Fetch order
        order = await self.uow.orders.get(order_id)
        if not order:
            raise BusinessError("Order not found")
        if order.payment_status == PaymentStatus.PAID:
            raise BusinessError("Order already paid")

        # Create payment record
        payment = await self.uow.payments.create(
            order_id=order_id,
            gateway=gateway,
            amount=order.grand_total,
            currency="BDT",
            status=PaymentStatus.PENDING
        )

        # Call gateway (stubbed)
        redirect_url = None
        transaction_id = None
        gateway_response = {}

        if gateway == PaymentGateway.SSLCOMMERZ:
            transaction_id = f"SSL_{payment.id.hex[:8]}"
            redirect_url = f"https://sandbox.sslcommerz.com/gwprocess/{transaction_id}"
            gateway_response = {"init": "success"}
        elif gateway == PaymentGateway.STRIPE:
            transaction_id = f"pi_{payment.id.hex[:8]}"
            redirect_url = f"https://checkout.stripe.com/{transaction_id}"
            gateway_response = {"client_secret": "mock_secret"}
        else:
            # COD: no redirect, mark as pending
            pass

        # Update payment
        payment.transaction_id = transaction_id
        payment.gateway_response = gateway_response
        await self.uow.commit()
        await self.uow.refresh(payment)

        return {
            "payment_id": payment.id,
            "order_id": order_id,
            "gateway": gateway,
            "redirect_url": redirect_url,
            "transaction_id": transaction_id
        }

    async def handle_webhook(self, gateway: PaymentGateway, payload: Dict[str, Any]):
        transaction_id: Optional[str] = None
        new_status: Optional[PaymentStatus] = None
        paid_at: Optional[datetime] = None

        if gateway == PaymentGateway.SSLCOMMERZ:
            transaction_id = payload.get("tran_id")
            status_str = payload.get("status")
            if status_str == "VALID":
                new_status = PaymentStatus.PAID
                paid_at = datetime.now(timezone.utc)
            else:
                new_status = PaymentStatus.FAILED

        elif gateway == PaymentGateway.STRIPE:
            event = payload
            if event.get("type") == "checkout.session.completed":
                transaction_id = event["data"]["object"]["id"]
                new_status = PaymentStatus.PAID
                paid_at = datetime.now(timezone.utc)
            else:
                new_status = PaymentStatus.FAILED

        else:
            raise BusinessError(f"Unsupported gateway: {gateway}")

        if transaction_id is None:
            raise BusinessError("Transaction ID missing in webhook")

        payment = await self.uow.payments.get_by_transaction_id(transaction_id)
        if not payment:
            raise BusinessError(f"Payment with transaction_id {transaction_id} not found")

        if new_status is not None:
            payment.status = new_status
        if paid_at is not None:
            payment.paid_at = paid_at
        payment.gateway_response = payload

        # Update order status
        order = await self.uow.orders.get(payment.order_id)
        if order and new_status is not None:
            order.payment_status = new_status
            if new_status == PaymentStatus.PAID:
                order.order_status = OrderStatus.PROCESSING
                # Trigger seller wallet credit (via event later)

        await self.uow.commit()
        await self.uow.refresh(payment)
        return payment

    async def get_payment_status(self, payment_id: UUID):
        payment = await self.uow.payments.get(payment_id)
        if not payment:
            raise BusinessError("Payment not found")
        return payment

    async def request_refund(self, payment_id: UUID, amount: Decimal, reason: Optional[str] = None):
        payment = await self.uow.payments.get(payment_id)
        if not payment:
            raise BusinessError("Payment not found")
        if payment.status != PaymentStatus.PAID:
            raise BusinessError("Payment not eligible for refund")

        # Create refund record
        refund = await self.uow.refunds.create(
            payment_id=payment_id,
            order_id=payment.order_id,
            amount=amount,
            reason=reason,
            status="pending"
        )

        # In production, call gateway refund API
        # For now, we'll just update status

        await self.uow.commit()
        await self.uow.refresh(refund)
        return refund