from dataclasses import dataclass
from uuid import UUID
from decimal import Decimal
from typing import List, Optional

@dataclass
class DomainEvent:
    pass

@dataclass
class OrderPlaced(DomainEvent):
    order_id: UUID
    user_id: UUID
    grand_total: Decimal

@dataclass
class PaymentSucceeded(DomainEvent):
    payment_id: UUID
    order_id: UUID
    amount: Decimal

@dataclass
class ProductApproved(DomainEvent):
    product_id: UUID
    seller_id: UUID

@dataclass
class SellerApproved(DomainEvent):
    seller_id: UUID
    user_id: UUID

@dataclass
class WithdrawalRequested(DomainEvent):
    request_id: UUID
    seller_id: UUID
    amount: Decimal

@dataclass
class OrderShipped(DomainEvent):
    order_id: UUID
    tracking_number: str

@dataclass
class ReviewSubmitted(DomainEvent):
    review_id: UUID
    product_id: UUID