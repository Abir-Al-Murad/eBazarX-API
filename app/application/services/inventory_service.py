from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import InsufficientStockError
from uuid import UUID

class InventoryService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def reserve_stock(self, variant_id: UUID, quantity: int, order_id: UUID):
        variant = await self.uow.variants.get(variant_id)
        if not variant:
            raise ValueError("Variant not found")
        if variant.stock - variant.reserved_stock < quantity:
            raise InsufficientStockError(f"Variant {variant.sku} has insufficient stock")
        variant.reserved_stock += quantity
        # log inventory
        await self.uow.inventory_logs.create(
            variant_id=variant_id,
            change_amount=-quantity,
            stock_before=variant.stock,
            stock_after=variant.stock - quantity,
            reason="order_placed",
            order_id=order_id
        )
        # Note: commit handled by UoW

    async def confirm_stock_deduction(self, order_id: UUID):
        # On payment success, decrement actual stock and move reserved to sold
        logs = await self.uow.inventory_logs.get_by_order(order_id)
        for log in logs:
            variant = await self.uow.variants.get(log.variant_id)
            if variant:
                variant.stock -= log.change_amount  # assuming negative change
                variant.reserved_stock += log.change_amount  # reverse reserve
                # create new log for actual deduction
                await self.uow.inventory_logs.create(
                    variant_id=variant.id,
                    change_amount=log.change_amount,
                    stock_before=variant.stock + log.change_amount,  # before deduction
                    stock_after=variant.stock,
                    reason="order_confirmed",
                    order_id=order_id
                )