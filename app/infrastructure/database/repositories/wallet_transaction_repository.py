from sqlalchemy import select
from uuid import UUID
from typing import Sequence, Optional
from app.infrastructure.database.models import WalletTransaction
from .base import AsyncBaseRepository

class WalletTransactionRepository(AsyncBaseRepository[WalletTransaction]):
    async def get_by_wallet(self, wallet_id: UUID, skip: int = 0, limit: int = 100) -> Sequence[WalletTransaction]:
        result = await self.session.execute(
            select(WalletTransaction)
            .filter(WalletTransaction.wallet_id == wallet_id)
            .offset(skip)
            .limit(limit)
            .order_by(WalletTransaction.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_reference(self, reference_id: UUID, reference_type: str) -> Optional[WalletTransaction]:
        result = await self.session.execute(
            select(WalletTransaction).filter(
                WalletTransaction.reference_id == reference_id,
                WalletTransaction.reference_type == reference_type
            )
        )
        return result.scalar_one_or_none()