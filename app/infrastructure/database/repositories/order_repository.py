from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, select, desc
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, Sequence, List
from app.infrastructure.database.models import Order, OrderStatus
from .base import AsyncBaseRepository

class OrderRepository(AsyncBaseRepository[Order]):
    async def get(self, id: UUID) -> Optional[Order]:
        stmt = (
            select(Order)
            .filter(Order.id == id, Order.deleted_at.is_(None))
            .options(
                selectinload(Order.items),
                selectinload(Order.user),   # Eager load user for safety
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[OrderStatus] = None,
    ) -> Sequence[Order]:
        stmt = select(Order).filter(Order.deleted_at.is_(None))
        if status:
            stmt = stmt.filter(Order.order_status == status)
        stmt = (
            stmt
            .offset(skip)
            .limit(limit)
            .order_by(desc(Order.created_at))
            .options(
                selectinload(Order.items),
                selectinload(Order.user),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> Sequence[Order]:
        stmt = (
            select(Order)
            .filter(Order.user_id == user_id, Order.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(desc(Order.created_at))
            .options(
                selectinload(Order.items),
                selectinload(Order.user),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_items(self, order_id: UUID) -> Optional[Order]:
        stmt = (
            select(Order)
            .filter(Order.id == order_id, Order.deleted_at.is_(None))
            .options(
                selectinload(Order.items),
                selectinload(Order.user),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_all(self) -> int:
        result = await self.session.execute(
            select(func.count()).filter(Order.deleted_at.is_(None))
        )
        return result.scalar() or 0

    async def count_by_status(self, status: OrderStatus) -> int:
        result = await self.session.execute(
            select(func.count()).filter(
                Order.order_status == status,
                Order.deleted_at.is_(None),
            )
        )
        return result.scalar() or 0

    async def sum_revenue_by_date(self, start_date: datetime, end_date: datetime) -> Decimal:
        result = await self.session.execute(
            select(func.sum(Order.grand_total)).filter(
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.deleted_at.is_(None),
                Order.order_status != OrderStatus.CANCELLED,
            )
        )
        return result.scalar() or Decimal(0)

    async def sum_revenue_all(self) -> Decimal:
        result = await self.session.execute(
            select(func.sum(Order.grand_total)).filter(
                Order.deleted_at.is_(None),
                Order.order_status != OrderStatus.CANCELLED,
            )
        )
        return result.scalar() or Decimal(0)

    async def get_recent(self, limit: int = 10) -> Sequence[Order]:
        stmt = (
            select(Order)
            .filter(Order.deleted_at.is_(None))
            .order_by(desc(Order.created_at))
            .limit(limit)
            .options(
                selectinload(Order.items),
                selectinload(Order.user),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()