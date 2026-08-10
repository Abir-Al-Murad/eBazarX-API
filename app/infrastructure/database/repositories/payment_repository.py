from celery import result
from sqlalchemy import select
from uuid import UUID
from typing import Optional
from app.infrastructure.database.models import Payment
from .base import AsyncBaseRepository

class PaymentRepository(AsyncBaseRepository[Payment]):
    async def get_by_order(self, order_id: UUID) -> Optional[Payment]:
        result = await self.session.execute(select(Payment).filter(Payment.order_id == order_id))
        return result.scalar_one_or_none()
    
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        result = await self.session.execute(
        select(Payment).filter(Payment.transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()
