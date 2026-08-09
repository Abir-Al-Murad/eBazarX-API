from uuid import UUID
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy import select, func, and_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # ✅ Required for eager loading

from app.infrastructure.database.unit_of_work import UnitOfWork
from app.infrastructure.database.models import (
    Order, OrderItem, Product, Seller, User, Review,
    SellerWallet, WithdrawRequest,
    Category, Brand, Coupon, Banner,
    OrderStatus, ProductApprovalStatus,
    SellerStatus, UserRole, WithdrawStatus
)


class DashboardService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ----- Seller Dashboard -----
    async def get_seller_dashboard(self, seller_id: UUID) -> Dict[str, Any]:
        """Fetch seller dashboard statistics using async aggregations."""
        session: AsyncSession = self.uow.session

        # 1. Order stats with case()
        stmt = select(
            func.count(OrderItem.id).label('total_orders'),
            func.sum(
                case((OrderItem.status == OrderStatus.DELIVERED, 1), else_=0)
            ).label('completed_orders'),
            func.sum(
                case((OrderItem.status == OrderStatus.PENDING, 1), else_=0)
            ).label('pending_orders'),
            func.sum(
                case((OrderItem.status == OrderStatus.CANCELLED, 1), else_=0)
            ).label('cancelled_orders'),
            func.sum(
                case(
                    (OrderItem.status.in_([OrderStatus.DELIVERED, OrderStatus.PROCESSING, OrderStatus.SHIPPED]),
                     OrderItem.price_at_time * OrderItem.quantity),
                    else_=0
                )
            ).label('total_revenue')
        ).where(OrderItem.seller_id == seller_id)

        result = await session.execute(stmt)
        row = result.one()
        total_orders = row.total_orders or 0
        completed_orders = row.completed_orders or 0
        pending_orders = row.pending_orders or 0
        cancelled_orders = row.cancelled_orders or 0
        total_revenue = row.total_revenue or Decimal('0.00')

        # 2. Product stats
        stmt = select(
            func.count(Product.id).label('total_products'),
            func.sum(
                case(
                    (and_(Product.is_active == True, Product.approval_status == ProductApprovalStatus.APPROVED), 1),
                    else_=0
                )
            ).label('active_products')
        ).where(Product.seller_id == seller_id)

        result = await session.execute(stmt)
        row = result.one()
        total_products = row.total_products or 0
        active_products = row.active_products or 0

        # 3. Review stats (aggregate over seller's products)
        stmt = select(
            func.count(Review.id).label('total_reviews'),
            func.avg(Review.rating).label('average_rating')
        ).join(Product, Product.id == Review.product_id)\
         .where(Product.seller_id == seller_id)\
         .where(Review.is_hidden == False)

        result = await session.execute(stmt)
        row = result.one()
        total_reviews = row.total_reviews or 0
        avg_rating = row.average_rating or Decimal('0.00')
        average_rating = Decimal(str(avg_rating)).quantize(Decimal('0.01'))

        # 4. Wallet (SellerWallet)
        stmt = select(SellerWallet).where(SellerWallet.seller_id == seller_id)
        wallet = (await session.execute(stmt)).scalar_one_or_none()
        available_balance = wallet.available_balance if wallet else Decimal('0.00')
        pending_balance = wallet.pending_balance if wallet else Decimal('0.00')

        # 5. Pending withdrawals
        stmt = select(func.count(WithdrawRequest.id)).where(
            WithdrawRequest.seller_id == seller_id,
            WithdrawRequest.status == WithdrawStatus.PENDING
        )
        pending_withdrawals = (await session.execute(stmt)).scalar() or 0

        return {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "pending_orders": pending_orders,
            "cancelled_orders": cancelled_orders,
            "total_revenue": float(total_revenue),
            "total_products": total_products,
            "active_products": active_products,
            "total_reviews": total_reviews,
            "average_rating": float(average_rating),
            "available_balance": float(available_balance),
            "pending_balance": float(pending_balance),
            "pending_withdrawals": pending_withdrawals,
        }

    async def get_seller_order_status_count(self, seller_id: UUID) -> List[Dict[str, Any]]:
        session = self.uow.session
        stmt = select(
            OrderItem.status,
            func.count(OrderItem.id).label('count')
        ).where(OrderItem.seller_id == seller_id)\
         .group_by(OrderItem.status)

        result = await session.execute(stmt)
        rows = result.all()
        return [{"status": r.status.value, "count": r.count} for r in rows]

    async def get_seller_top_products(self, seller_id: UUID, limit: int = 5) -> List[Dict[str, Any]]:
        session = self.uow.session
        stmt = select(
            OrderItem.product_id,
            OrderItem.product_name_at_time,
            func.sum(OrderItem.quantity).label('total_sales'),
            func.sum(OrderItem.price_at_time * OrderItem.quantity).label('revenue')
        ).where(OrderItem.seller_id == seller_id)\
         .group_by(OrderItem.product_id, OrderItem.product_name_at_time)\
         .order_by(desc(func.sum(OrderItem.price_at_time * OrderItem.quantity)))\
         .limit(limit)

        result = await session.execute(stmt)
        rows = result.all()
        return [
            {
                "product_id": str(r.product_id),
                "product_name": r.product_name_at_time,
                "total_sales": r.total_sales,
                "revenue": float(r.revenue or 0)
            }
            for r in rows
        ]

    # ----- Admin Dashboard -----
    async def get_admin_dashboard(self) -> Dict[str, Any]:
        session = self.uow.session

        # 1. User counts
        stmt = select(
            func.count(User.id).label('total'),
            func.sum(case((User.role == UserRole.CUSTOMER, 1), else_=0)).label('customers'),
            func.sum(case((User.role == UserRole.SELLER, 1), else_=0)).label('sellers')
        )
        result = await session.execute(stmt)
        row = result.one()
        total_customers = row.customers or 0
        total_sellers = row.sellers or 0

        # 2. Pending sellers
        stmt = select(func.count(Seller.id)).where(Seller.status == SellerStatus.PENDING)
        pending_sellers = (await session.execute(stmt)).scalar() or 0

        # 3. Products & pending approval
        stmt = select(
            func.count(Product.id).label('total'),
            func.sum(case((Product.approval_status == ProductApprovalStatus.PENDING, 1), else_=0)).label('pending')
        )
        result = await session.execute(stmt)
        row = result.one()
        total_products = row.total or 0
        pending_products = row.pending or 0

        # 4. Orders
        stmt = select(
            func.count(Order.id).label('total'),
            func.sum(case((Order.order_status == OrderStatus.PENDING, 1), else_=0)).label('pending'),
            func.sum(case((Order.order_status == OrderStatus.DELIVERED, 1), else_=0)).label('completed'),
            func.sum(case((Order.order_status == OrderStatus.CANCELLED, 1), else_=0)).label('cancelled')
        )
        result = await session.execute(stmt)
        row = result.one()
        total_orders = row.total or 0
        pending_orders = row.pending or 0
        completed_orders = row.completed or 0
        cancelled_orders = row.cancelled or 0

        # 5. Total revenue
        stmt = select(func.sum(Order.grand_total)).where(
            Order.order_status.in_([OrderStatus.DELIVERED, OrderStatus.PROCESSING])
        )
        total_revenue = (await session.execute(stmt)).scalar() or Decimal('0.00')

        # 6. Today's stats
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(
            func.count(Order.id).label('orders'),
            func.sum(Order.grand_total).label('revenue')
        ).where(
            Order.created_at >= today_start,
            Order.order_status.in_([OrderStatus.DELIVERED, OrderStatus.PROCESSING])
        )
        result = await session.execute(stmt)
        row = result.one()
        today_orders = row.orders or 0
        today_revenue = row.revenue or Decimal('0.00')

        # 7. Reviews
        stmt = select(func.count(Review.id)).where(Review.is_hidden == False)
        total_reviews = (await session.execute(stmt)).scalar() or 0

        # 8. Categories, Brands, Coupons, Banners
        total_categories = (await session.execute(select(func.count('*')).select_from(Category))).scalar() or 0
        total_brands = (await session.execute(select(func.count('*')).select_from(Brand))).scalar() or 0
        total_coupons = (await session.execute(select(func.count('*')).select_from(Coupon))).scalar() or 0
        total_banners = (await session.execute(select(func.count('*')).select_from(Banner))).scalar() or 0

        return {
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "total_products": total_products,
            "total_customers": total_customers,
            "total_sellers": total_sellers,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "total_reviews": total_reviews,
            "total_coupons": total_coupons,
            "total_banners": total_banners,
            "total_categories": total_categories,
            "total_brands": total_brands,
            "pending_sellers": pending_sellers,
            "pending_products": pending_products,
            "today_orders": today_orders,
            "today_revenue": float(today_revenue),
        }

    async def get_admin_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        session = self.uow.session
        stmt = (
            select(Order)
            .order_by(desc(Order.created_at))
            .limit(limit)
            .options(selectinload(Order.user))  # ✅ Eager load user
        )
        result = await session.execute(stmt)
        orders = result.scalars().all()
        return [
            {
                "id": str(o.id),                    # ✅ Use UUID as order identifier
                "grand_total": float(o.grand_total),
                "order_status": o.order_status.value,
                "created_at": o.created_at.isoformat(),
                "customer_name": o.user.full_name if o.user else None,
            }
            for o in orders
        ]

    async def get_admin_top_sellers(self, limit: int = 5) -> List[Dict[str, Any]]:
        session = self.uow.session
        stmt = select(
            Seller.id,
            Seller.shop_name,
            func.sum(OrderItem.price_at_time * OrderItem.quantity).label('total_revenue'),
            func.count(OrderItem.id).label('total_orders')
        ).join(OrderItem, OrderItem.seller_id == Seller.id)\
         .where(OrderItem.status.in_([OrderStatus.DELIVERED, OrderStatus.PROCESSING]))\
         .group_by(Seller.id, Seller.shop_name)\
         .order_by(desc(func.sum(OrderItem.price_at_time * OrderItem.quantity)))\
         .limit(limit)

        result = await session.execute(stmt)
        rows = result.all()
        return [
            {
                "seller_id": str(r.id),
                "shop_name": r.shop_name,
                "total_revenue": float(r.total_revenue or 0),
                "total_orders": r.total_orders or 0
            }
            for r in rows
        ]

    async def get_admin_top_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        session = self.uow.session
        stmt = select(
            OrderItem.product_id,
            OrderItem.product_name_at_time,
            func.sum(OrderItem.quantity).label('total_sales'),
            func.sum(OrderItem.price_at_time * OrderItem.quantity).label('revenue')
        ).group_by(OrderItem.product_id, OrderItem.product_name_at_time)\
         .order_by(desc(func.sum(OrderItem.price_at_time * OrderItem.quantity)))\
         .limit(limit)

        result = await session.execute(stmt)
        rows = result.all()
        return [
            {
                "product_id": str(r.product_id),
                "product_name": r.product_name_at_time,
                "total_sales": r.total_sales or 0,
                "revenue": float(r.revenue or 0)
            }
            for r in rows
        ]

    async def get_admin_revenue_by_period(self, days: int = 30) -> List[Dict[str, Any]]:
        session = self.uow.session
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = select(Order).where(Order.created_at >= cutoff)
        result = await session.execute(stmt)
        orders = result.scalars().all()

        revenue_by_day = {}
        for i in range(days):
            day = (datetime.now(timezone.utc) - timedelta(days=i)).date()
            day_key = day.isoformat()
            revenue_by_day[day_key] = {"period": day_key, "revenue": Decimal(0), "orders": 0}

        for order in orders:
            day_key = order.created_at.date().isoformat()
            if day_key in revenue_by_day:
                revenue_by_day[day_key]["revenue"] += order.grand_total
                revenue_by_day[day_key]["orders"] += 1

        result_list = sorted(revenue_by_day.values(), key=lambda x: x["period"])
        for item in result_list:
            item["revenue"] = float(item["revenue"])
        return result_list