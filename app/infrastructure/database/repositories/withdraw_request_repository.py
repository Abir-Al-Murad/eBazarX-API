from sqlalchemy import select
from uuid import UUID
from typing import Sequence, Optional
from app.infrastructure.database.models import WithdrawRequest, WithdrawStatus
from .base import AsyncBaseRepository

class WithdrawRequestRepository(AsyncBaseRepository[WithdrawRequest]):
    async def get_by_seller(self, seller_id: UUID, skip: int = 0, limit: int = 50) -> Sequence[WithdrawRequest]:
        result = await self.session.execute(
            select(WithdrawRequest)
            .filter(WithdrawRequest.seller_id == seller_id)
            .order_by(WithdrawRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_status(self, status: WithdrawStatus, skip: int = 0, limit: int = 50) -> Sequence[WithdrawRequest]:
        result = await self.session.execute(
            select(WithdrawRequest)
            .filter(WithdrawRequest.status == status)
            .order_by(WithdrawRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()