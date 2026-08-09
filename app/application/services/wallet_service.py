from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List, Sequence
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.infrastructure.database.models import SellerWallet, WalletTransaction, WalletTransactionType, WithdrawStatus
from app.api.v1.schemas.wallet import WithdrawalRequestCreate

class WalletService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ----- Wallet Operations -----
    async def get_or_create_wallet(self, seller_id: UUID) -> SellerWallet:
        wallet = await self.uow.wallets.get_by_seller(seller_id)
        if not wallet:
            wallet = await self.uow.wallets.create(seller_id=seller_id)
            await self.uow.commit()
            await self.uow.refresh(wallet)
        return wallet

    async def get_wallet(self, seller_id: UUID) -> SellerWallet:
        wallet = await self.uow.wallets.get_by_seller(seller_id)
        if not wallet:
            raise BusinessError("Wallet not found")
        return wallet

    async def get_transactions(self, seller_id: UUID, skip: int = 0, limit: int = 50) -> Sequence[WalletTransaction]:
        wallet = await self.get_wallet(seller_id)
        return await self.uow.wallet_transactions.get_by_wallet(wallet.id, skip, limit)

    # ----- Credit seller (called after payment confirmation) -----
    async def credit_seller(self, seller_id: UUID, amount: Decimal, order_id: UUID, commission: Decimal = Decimal(0)):
        wallet = await self.get_or_create_wallet(seller_id)
        balance_before = wallet.pending_balance + wallet.available_balance

        wallet.pending_balance += amount
        if commission:
            wallet.commission_paid += commission
        wallet.lifetime_earnings += amount

        await self.uow.wallet_transactions.create(
            wallet_id=wallet.id,
            type=WalletTransactionType.ORDER_CREDIT,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.pending_balance + wallet.available_balance,
            description=f"Earnings from order {order_id}",
            reference_id=order_id,
            reference_type="order"
        )
        await self.uow.commit()

    # ----- Move pending to available (after delivery confirmation) -----
    async def release_pending_balance(self, seller_id: UUID, amount: Decimal, order_id: UUID):
        wallet = await self.get_wallet(seller_id)
        if wallet.pending_balance < amount:
            raise BusinessError("Insufficient pending balance")

        wallet.pending_balance -= amount
        wallet.available_balance += amount

        await self.uow.wallet_transactions.create(
            wallet_id=wallet.id,
            type=WalletTransactionType.DEPOSIT,
            amount=amount,
            balance_before=wallet.pending_balance + wallet.available_balance - amount,
            balance_after=wallet.pending_balance + wallet.available_balance,
            description=f"Balance released from order {order_id}",
            reference_id=order_id,
            reference_type="order"
        )
        await self.uow.commit()

    # ----- Withdrawal -----
    async def request_withdrawal(self, seller_id: UUID, data: WithdrawalRequestCreate):
        wallet = await self.get_wallet(seller_id)
        if wallet.available_balance < data.amount:
            raise BusinessError("Insufficient available balance")

        withdrawal = await self.uow.withdraw_requests.create(
            seller_id=seller_id,
            amount=data.amount,
            method=data.method,
            account_info=data.account_info,
            status=WithdrawStatus.PENDING
        )

        wallet.available_balance -= data.amount
        wallet.locked_balance += data.amount

        await self.uow.wallet_transactions.create(
            wallet_id=wallet.id,
            type=WalletTransactionType.WITHDRAWAL,
            amount=-data.amount,
            balance_before=wallet.available_balance + wallet.locked_balance - data.amount,
            balance_after=wallet.available_balance + wallet.locked_balance,
            description=f"Withdrawal request {withdrawal.id}",
            reference_id=withdrawal.id,
            reference_type="withdrawal"
        )
        await self.uow.commit()
        await self.uow.refresh(withdrawal)
        return withdrawal

    async def approve_withdrawal(self, withdrawal_id: UUID, admin_notes: Optional[str] = None):
        withdrawal = await self.uow.withdraw_requests.get(withdrawal_id)
        if not withdrawal:
            raise BusinessError("Withdrawal request not found")
        if withdrawal.status != WithdrawStatus.PENDING:
            raise BusinessError("Withdrawal already processed")

        wallet = await self.get_wallet(withdrawal.seller_id)

        wallet.locked_balance -= withdrawal.amount
        wallet.withdrawn_total += withdrawal.amount

        withdrawal.status = WithdrawStatus.COMPLETED
        withdrawal.processed_at = datetime.now(timezone.utc)
        withdrawal.admin_notes = admin_notes

        await self.uow.wallet_transactions.create(
            wallet_id=wallet.id,
            type=WalletTransactionType.WITHDRAWAL,
            amount=withdrawal.amount,
            balance_before=wallet.available_balance + wallet.locked_balance + withdrawal.amount,
            balance_after=wallet.available_balance + wallet.locked_balance,
            description=f"Withdrawal approved: {withdrawal.id}",
            reference_id=withdrawal.id,
            reference_type="withdrawal"
        )
        await self.uow.commit()
        await self.uow.refresh(withdrawal)
        return withdrawal

    async def reject_withdrawal(self, withdrawal_id: UUID, admin_notes: Optional[str] = None):
        withdrawal = await self.uow.withdraw_requests.get(withdrawal_id)
        if not withdrawal:
            raise BusinessError("Withdrawal request not found")
        if withdrawal.status != WithdrawStatus.PENDING:
            raise BusinessError("Withdrawal already processed")

        wallet = await self.get_wallet(withdrawal.seller_id)

        wallet.locked_balance -= withdrawal.amount
        wallet.available_balance += withdrawal.amount

        withdrawal.status = WithdrawStatus.REJECTED
        withdrawal.admin_notes = admin_notes

        await self.uow.wallet_transactions.create(
            wallet_id=wallet.id,
            type=WalletTransactionType.ADJUSTMENT,
            amount=withdrawal.amount,
            balance_before=wallet.available_balance + wallet.locked_balance - withdrawal.amount,
            balance_after=wallet.available_balance + wallet.locked_balance,
            description=f"Withdrawal rejected: {withdrawal.id}",
            reference_id=withdrawal.id,
            reference_type="withdrawal"
        )
        await self.uow.commit()
        await self.uow.refresh(withdrawal)
        return withdrawal

    # ----- Unified process method (for Admin approval/rejection) -----
    async def process_withdrawal(
        self,
        withdrawal_id: UUID,
        status: WithdrawStatus,
        admin_notes: Optional[str] = None,
    ):
        if status == WithdrawStatus.COMPLETED:
            return await self.approve_withdrawal(withdrawal_id, admin_notes)

        if status == WithdrawStatus.REJECTED:
            return await self.reject_withdrawal(withdrawal_id, admin_notes)

        raise BusinessError("Invalid withdrawal status")