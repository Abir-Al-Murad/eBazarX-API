from decimal import Decimal

from sqlalchemy import select
from uuid import UUID
from typing import Optional
from app.api.v1.schemas import wallet
from app.infrastructure.database.models import SellerWallet
from .base import AsyncBaseRepository

class WalletRepository(AsyncBaseRepository[SellerWallet]):
    async def get_by_seller(self, seller_id: UUID) -> Optional[SellerWallet]:
        result = await self.session.execute(select(SellerWallet).filter(SellerWallet.seller_id == seller_id))
        return result.scalar_one_or_none()
    
    async def update_balances(
    self,
    wallet_id: UUID,
    available_delta: Decimal = Decimal(0),
    pending_delta: Decimal = Decimal(0),
    locked_delta: Decimal = Decimal(0),
    withdrawn_delta: Decimal = Decimal(0),
    lifetime_delta: Decimal = Decimal(0),
    commission_delta: Decimal = Decimal(0)
    ) -> Optional[SellerWallet]:
        wallet = await self.get(wallet_id)
        if not wallet:
            return None

        wallet.available_balance += available_delta
        wallet.pending_balance += pending_delta
        wallet.locked_balance += locked_delta
        wallet.withdrawn_total += withdrawn_delta
        wallet.lifetime_earnings += lifetime_delta
        wallet.commission_paid += commission_delta

        await self.session.commit()
        await self.session.refresh(wallet)
        return wallet