from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

class DashboardStats(BaseModel):
    total_orders: int = 0
    total_revenue: Decimal = Decimal(0)
    total_products: int = 0
    total_customers: int = 0
    pending_orders: int = 0
    completed_orders: int = 0
    cancelled_orders: int = 0

class SellerDashboardStats(DashboardStats):
    average_rating: Decimal = Decimal(0)
    total_reviews: int = 0
    pending_withdrawals: int = 0
    available_balance: Decimal = Decimal(0)
    pending_balance: Decimal = Decimal(0)

class AdminDashboardStats(DashboardStats):
    total_sellers: int = 0
    total_reviews: int = 0
    total_coupons: int = 0
    total_banners: int = 0
    total_categories: int = 0
    total_brands: int = 0
    pending_sellers: int = 0
    pending_products: int = 0
    today_orders: int = 0
    today_revenue: Decimal = Decimal(0)

class OrderStatusCount(BaseModel):
    status: str
    count: int

class RevenueByPeriod(BaseModel):
    period: str
    revenue: Decimal
    orders: int

class TopProduct(BaseModel):
    product_id: UUID
    product_name: str
    total_sales: int
    revenue: Decimal

class TopSeller(BaseModel):
    seller_id: UUID
    shop_name: str
    total_revenue: Decimal
    total_orders: int