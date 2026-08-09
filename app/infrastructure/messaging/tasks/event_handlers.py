from celery import shared_task
from app.domain.events import OrderPlaced, PaymentSucceeded, ProductApproved
import logging

logger = logging.getLogger(__name__)

@shared_task(name="handle_orderplaced")
def handle_order_placed(event: OrderPlaced):
    # In real code, we would inject services or use a task context to get UoW.
    # For now, placeholder.
    logger.info(f"Order placed: {event.order_id} for user {event.user_id} amount {event.grand_total}")
    # Example: send email, update statistics, etc.
    # We'll call other services via Celery chain.

@shared_task(name="handle_paymentsucceeded")
def handle_payment_succeeded(event: PaymentSucceeded):
    logger.info(f"Payment succeeded for order {event.order_id}")
    # Credit seller wallets, update order status, send notifications.

@shared_task(name="handle_productapproved")
def handle_product_approved(event: ProductApproved):
    logger.info(f"Product approved: {event.product_id}")
    # Update search index, notify seller.