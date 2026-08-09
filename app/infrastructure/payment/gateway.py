from app.domain.events import PaymentSucceeded
from app.domain.interfaces.event_bus import EventBus
from uuid import UUID
from decimal import Decimal

class PaymentGatewayService:
    async def initiate_payment(self, order_id: UUID, amount: Decimal, method: str):
        # Stub – integrate with SSLCommerz, Stripe, etc.
        # Return redirect URL or payment intent.
        return {"payment_url": "https://payment.example.com/123"}