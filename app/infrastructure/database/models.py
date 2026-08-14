from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey,
    Enum, JSON, Numeric, Index, UniqueConstraint, CheckConstraint, ARRAY, Date
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from decimal import Decimal

Base = declarative_base()

# Mixins
class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

# Enums
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SELLER = "seller"
    CUSTOMER = "customer"

class SellerStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class ProductApprovalStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentGateway(str, enum.Enum):
    COD = "cod"
    SSLCOMMERZ = "sslcommerz"
    STRIPE = "stripe"
    BKASH = "bkash"
    NAGAD = "nagad"
    ROCKET = "rocket"

class DiscountType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"

class WithdrawStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    REJECTED = "rejected"

class NotificationType(str, enum.Enum):
    ORDER = "order"
    PAYMENT = "payment"
    PROMOTION = "promotion"
    SYSTEM = "system"
    SELLER = "seller"

class WalletTransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    COMMISSION = "commission"
    WITHDRAWAL = "withdrawal"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    ORDER_CREDIT = "order_credit"

class InventoryReason(str, enum.Enum):
    ORDER_PLACED = "order_placed"
    ORDER_CANCELLED = "order_cancelled"
    RESTOCK = "restock"
    ADJUSTMENT = "adjustment"
    RETURN = "return"

# ---------- Models ----------

class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_image: Mapped[Optional[str]] = mapped_column(String(500))
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(Date)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    cart = relationship("Cart", back_populates="user", uselist=False)
    wishlist = relationship("Wishlist", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    seller = relationship("Seller", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")
    email_verifications = relationship("EmailVerification", back_populates="user")
    notification_preference = relationship("NotificationPreference", back_populates="user", uselist=False)
    activity_logs = relationship("ActivityLog", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    inventory_logs_admin = relationship("InventoryLog", foreign_keys="InventoryLog.admin_user_id", back_populates="admin")
    coupon_usages = relationship("CouponUsage", back_populates="user")

class RefreshToken(Base, UUIDMixin):
    __tablename__ = "refresh_tokens"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user = relationship("User", back_populates="refresh_tokens")

class UserSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_sessions"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    user = relationship("User", back_populates="sessions")

class PasswordResetToken(Base, UUIDMixin):
    __tablename__ = "password_reset_tokens"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user = relationship("User", back_populates="password_reset_tokens")

class EmailVerification(Base, UUIDMixin):
    __tablename__ = "email_verifications"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user = relationship("User", back_populates="email_verifications")

class Seller(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "sellers"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    shop_name: Mapped[str] = mapped_column(String(255), nullable=False)
    shop_slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    logo: Mapped[Optional[str]] = mapped_column(String(500))
    cover_image: Mapped[Optional[str]] = mapped_column(String(500))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="Bangladesh")
    trade_license: Mapped[Optional[str]] = mapped_column(String(100))
    nid: Mapped[Optional[str]] = mapped_column(String(50))
    tin: Mapped[Optional[str]] = mapped_column(String(50))
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5,2), default=10.00)
    status: Mapped[SellerStatus] = mapped_column(Enum(SellerStatus), default=SellerStatus.PENDING, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="seller")
    wallet = relationship("SellerWallet", back_populates="seller", uselist=False)
    bank_accounts = relationship("SellerBankAccount", back_populates="seller")
    withdraw_requests = relationship("WithdrawRequest", back_populates="seller")
    products = relationship("Product", back_populates="seller")
    coupons = relationship("Coupon", back_populates="seller")
    order_items = relationship("OrderItem", back_populates="seller")
    statistics = relationship("SellerStatistics", back_populates="seller", uselist=False)
    average_rating: Mapped[Decimal] = mapped_column(Numeric(3,2), default=0)
    total_products: Mapped[int] = mapped_column(Integer, default=0)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)

class SellerWallet(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "seller_wallets"
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), unique=True, nullable=False)
    available_balance: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    pending_balance: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    locked_balance: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    withdrawn_total: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    lifetime_earnings: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    commission_paid: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    seller = relationship("Seller", back_populates="wallet")
    transactions = relationship("WalletTransaction", back_populates="wallet")

class WalletTransaction(Base, UUIDMixin):
    __tablename__ = "wallet_transactions"
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seller_wallets.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[WalletTransactionType] = mapped_column(Enum(WalletTransactionType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    reference_type: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    wallet = relationship("SellerWallet", back_populates="transactions")

class SellerBankAccount(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "seller_bank_accounts"
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_holder: Mapped[str] = mapped_column(String(255), nullable=False)
    account_number: Mapped[str] = mapped_column(String(100), nullable=False)
    branch: Mapped[Optional[str]] = mapped_column(String(255))
    routing_number: Mapped[Optional[str]] = mapped_column(String(50))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seller = relationship("Seller", back_populates="bank_accounts")

class WithdrawRequest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "withdraw_requests"
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    method: Mapped[str] = mapped_column(String(50), nullable=False)
    account_info: Mapped[Dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[WithdrawStatus] = mapped_column(Enum(WithdrawStatus), default=WithdrawStatus.PENDING, nullable=False)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    seller = relationship("Seller", back_populates="withdraw_requests")

    __table_args__ = (
        CheckConstraint("amount > 0", name="withdraw_amount_positive"),
    )

class SellerStatistics(Base, UUIDMixin):
    __tablename__ = "seller_statistics"
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_products: Mapped[int] = mapped_column(Integer, default=0)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0)
    total_followers: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[Decimal] = mapped_column(Numeric(3,2), default=0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    visitors_count: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[Decimal] = mapped_column(Numeric(5,2), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    seller = relationship("Seller", back_populates="statistics")

class Category(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "categories"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parent = relationship(
    "Category",
    remote_side=lambda: [Category.id],
    backref="children",
    )
    products = relationship("Product", back_populates="category")
    banners = relationship("Banner", back_populates="category")
    coupon_categories = relationship("CouponCategory", back_populates="category")

class Brand(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "brands"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    logo: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    products = relationship("Product", back_populates="brand")

class Product(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    discount_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12,2))
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    seo_title: Mapped[Optional[str]] = mapped_column(String(255))
    seo_description: Mapped[Optional[str]] = mapped_column(Text)
    meta_keywords: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(8,2))
    dimensions: Mapped[Optional[Dict]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approval_status: Mapped[ProductApprovalStatus] = mapped_column(Enum(ProductApprovalStatus), default=ProductApprovalStatus.PENDING, nullable=False)

    seller = relationship("Seller", back_populates="products")
    category = relationship("Category", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    statistics = relationship("ProductStatistics", back_populates="product", uselist=False)
    reviews = relationship("Review", back_populates="product")
    questions = relationship("ProductQuestion", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    wishlist_items = relationship("WishlistItem", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")
    coupon_products = relationship("CouponProduct", back_populates="product")
    flash_sale_products = relationship("FlashSaleProduct", back_populates="product")
    banners = relationship("Banner", back_populates="product")

    __table_args__ = (
        CheckConstraint("price >= 0", name="product_price_positive"),
        CheckConstraint("discount_price IS NULL OR discount_price <= price", name="product_discount_valid"),
    )

class ProductImage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_images"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    product = relationship("Product", back_populates="images")

class ProductAttribute(Base, UUIDMixin):
    __tablename__ = "product_attributes"
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    values = relationship("AttributeValue", back_populates="attribute")

class AttributeValue(Base, UUIDMixin):
    __tablename__ = "attribute_values"
    attribute_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_attributes.id", ondelete="CASCADE"), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    attribute = relationship("ProductAttribute", back_populates="values")
    variant_values = relationship("ProductVariantValue", back_populates="attribute_value")

    __table_args__ = (
        UniqueConstraint("attribute_id", "value", name="uq_attr_value"),
    )

class ProductVariant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_variants"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    price_override: Mapped[Optional[Decimal]] = mapped_column(Numeric(12,2))
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attributes: Mapped[Optional[Dict]] = mapped_column(JSONB)

    product = relationship("Product", back_populates="variants")
    variant_values = relationship("ProductVariantValue", back_populates="variant")
    inventory_logs = relationship("InventoryLog", back_populates="variant")
    cart_items = relationship("CartItem", back_populates="variant")
    wishlist_items = relationship("WishlistItem", back_populates="variant")
    order_items = relationship("OrderItem", back_populates="variant")

    __table_args__ = (
        CheckConstraint("stock >= 0", name="variant_stock_positive"),
        CheckConstraint("reserved_stock >= 0", name="variant_reserved_stock_positive"),
        CheckConstraint("reserved_stock <= stock", name="variant_reserved_not_exceed_stock"),
    )

class ProductVariantValue(Base, UUIDMixin):
    __tablename__ = "product_variant_values"
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    attribute_value_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attribute_values.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    variant = relationship("ProductVariant", back_populates="variant_values")
    attribute_value = relationship("AttributeValue", back_populates="variant_values")

    __table_args__ = (
        UniqueConstraint("variant_id", "attribute_value_id", name="uq_variant_attr_value"),
    )

class InventoryLog(Base, UUIDMixin):
    __tablename__ = "inventory_logs"
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    change_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_before: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[InventoryReason] = mapped_column(Enum(InventoryReason), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(255))
    admin_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    variant = relationship("ProductVariant", back_populates="inventory_logs")
    admin = relationship("User", foreign_keys=[admin_user_id], back_populates="inventory_logs_admin")
    order = relationship("Order", foreign_keys=[order_id], back_populates="inventory_logs")

class ProductStatistics(Base, UUIDMixin):
    __tablename__ = "product_statistics"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False)
    average_rating: Mapped[Decimal] = mapped_column(Numeric(3,2), default=0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    wishlist_count: Mapped[int] = mapped_column(Integer, default=0)
    cart_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    product = relationship("Product", back_populates="statistics")

class ProductQuestion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_questions"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text)
    product = relationship("Product", back_populates="questions")
    user = relationship("User")

# ============================
# Review Module Models
# ============================

class Review(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "reviews"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"))
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    dislikes: Mapped[int] = mapped_column(Integer, default=0)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Admin hide
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="review_rating_range"),
        # Unique per user per product per order (one review per order item)
        UniqueConstraint("user_id", "product_id", "order_id", name="uq_user_product_order"),
    )

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    order = relationship("Order")
    images = relationship("ReviewImage", back_populates="review", cascade="all, delete-orphan")
    votes = relationship("ReviewVote", back_populates="review", cascade="all, delete-orphan")
    reports = relationship("ReviewReport", back_populates="review", cascade="all, delete-orphan")
    reply = relationship(
        "ReviewReply",
        back_populates="review",
        uselist=False,
        cascade="all, delete-orphan"
    )


class ReviewImage(Base, UUIDMixin):
    __tablename__ = "review_images"
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    review = relationship("Review", back_populates="images")


class ReviewVote(Base, UUIDMixin):
    __tablename__ = "review_votes"
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vote_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'like' or 'dislike'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("review_id", "user_id", name="uq_review_vote"),
    )

    review = relationship("Review", back_populates="votes")
    user = relationship("User")


class ReviewReport(Base, UUIDMixin):
    __tablename__ = "review_reports"
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("review_id", "user_id", name="uq_review_report"),
    )

    review = relationship("Review", back_populates="reports")
    user = relationship("User")


class ReviewReply(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "review_replies"

    review_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sellers.id", ondelete="CASCADE"),
        nullable=False
    )

    reply: Mapped[str] = mapped_column(Text, nullable=False)


    review = relationship(
        "Review",
        back_populates="reply"
    )

    seller = relationship(
        "Seller"
    )
class Address(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "addresses"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    division: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(100))
    upazila: Mapped[Optional[str]] = mapped_column(String(100))
    area: Mapped[Optional[str]] = mapped_column(String(255))
    address_line: Mapped[str] = mapped_column(Text, nullable=False)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    label: Mapped[str] = mapped_column(String(50), default="Home")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user = relationship("User", back_populates="addresses")
    orders = relationship("Order", back_populates="address")

class Cart(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "carts"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

class CartItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cart_items"
    cart_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint("cart_id", "variant_id", name="uq_cart_item"),
        CheckConstraint("quantity > 0", name="cart_item_quantity_positive"),
    )

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")
    variant = relationship("ProductVariant", back_populates="cart_items")

class Wishlist(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wishlists"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    user = relationship("User", back_populates="wishlist")
    items = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan")

class WishlistItem(Base, UUIDMixin):
    __tablename__ = "wishlist_items"
    wishlist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wishlists.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("wishlist_id", "variant_id", name="uq_wishlist_item"),
    )

    wishlist = relationship("Wishlist", back_populates="items")
    product = relationship("Product", back_populates="wishlist_items")
    variant = relationship("ProductVariant", back_populates="wishlist_items")

class Order(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "orders"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    address_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    shipping_fee: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0, nullable=False)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    order_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100))
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    coupon_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("coupons.id", ondelete="SET NULL"))
    payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user = relationship("User", back_populates="orders")
    address = relationship("Address", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)
    shipment = relationship("Shipment", back_populates="order", uselist=False)
    refund = relationship("Refund", back_populates="order", uselist=False)
    inventory_logs = relationship("InventoryLog", foreign_keys="InventoryLog.order_id", back_populates="order")
    coupon_usages = relationship("CouponUsage", back_populates="order")

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="order_subtotal_positive"),
        CheckConstraint("shipping_fee >= 0", name="order_shipping_fee_positive"),
        CheckConstraint("tax >= 0", name="order_tax_positive"),
        CheckConstraint("discount_amount >= 0", name="order_discount_amount_positive"),
        CheckConstraint("grand_total >= 0", name="order_grand_total_positive"),
    )

class OrderItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "order_items"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_at_time: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    product_name_at_time: Mapped[str] = mapped_column(String(255), nullable=False)
    product_image_at_time: Mapped[Optional[str]] = mapped_column(String(500))
    size_at_time: Mapped[Optional[str]] = mapped_column(String(100))
    color_at_time: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    variant = relationship("ProductVariant", back_populates="order_items")
    seller = relationship("Seller", back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="order_item_quantity_positive"),
    )

class Shipment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "shipments"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    carrier: Mapped[Optional[str]] = mapped_column(String(100))
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100))
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    order = relationship("Order", back_populates="shipment")
    tracking_events = relationship("ShipmentTracking", back_populates="shipment", cascade="all, delete-orphan")

class ShipmentTracking(Base, UUIDMixin):
    __tablename__ = "shipment_tracking"
    shipment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    shipment = relationship("Shipment", back_populates="tracking_events")

class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    gateway: Mapped[PaymentGateway] = mapped_column(Enum(PaymentGateway), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="BDT")
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    gateway_response: Mapped[Optional[Dict]] = mapped_column(JSONB)

    order = relationship("Order", back_populates="payment")
    attempts = relationship("PaymentAttempt", back_populates="payment", cascade="all, delete-orphan")
    transactions = relationship("PaymentTransaction", back_populates="payment", cascade="all, delete-orphan")
    refund = relationship("Refund", back_populates="payment", uselist=False)

    __table_args__ = (
        CheckConstraint("amount > 0", name="payment_amount_positive"),
    )

class PaymentAttempt(Base, UUIDMixin):
    __tablename__ = "payment_attempts"
    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    request_data: Mapped[Optional[Dict]] = mapped_column(JSONB)
    response_data: Mapped[Optional[Dict]] = mapped_column(JSONB)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    payment = relationship("Payment", back_populates="attempts")

class PaymentTransaction(Base, UUIDMixin):
    __tablename__ = "payment_transactions"
    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    gateway_reference: Mapped[Optional[str]] = mapped_column(String(255))
    request_data: Mapped[Optional[Dict]] = mapped_column(JSONB)
    response_data: Mapped[Optional[Dict]] = mapped_column(JSONB)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    payment = relationship("Payment", back_populates="transactions")

class Refund(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "refunds"
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    order = relationship("Order", back_populates="refund")
    payment = relationship("Payment", back_populates="refund")

class Coupon(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "coupons"
    seller_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    discount_type: Mapped[DiscountType] = mapped_column(Enum(DiscountType), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    min_order_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12,2))
    max_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12,2))
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer)
    per_user_limit: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    seller = relationship("Seller", back_populates="coupons")
    usages = relationship("CouponUsage", back_populates="coupon", cascade="all, delete-orphan")
    products = relationship("CouponProduct", back_populates="coupon", cascade="all, delete-orphan")
    categories = relationship("CouponCategory", back_populates="coupon", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("start_date < end_date", name="coupon_date_valid"),
    )

class CouponProduct(Base, UUIDMixin):
    __tablename__ = "coupon_products"
    coupon_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("coupon_id", "product_id", name="uq_coupon_product"),
    )

    coupon = relationship("Coupon", back_populates="products")
    product = relationship("Product", back_populates="coupon_products")

class CouponCategory(Base, UUIDMixin):
    __tablename__ = "coupon_categories"
    coupon_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("coupon_id", "category_id", name="uq_coupon_category"),
    )

    coupon = relationship("Coupon", back_populates="categories")
    category = relationship("Category", back_populates="coupon_categories")

class CouponUsage(Base, UUIDMixin):
    __tablename__ = "coupon_usage"
    coupon_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("coupon_id", "user_id", "order_id", name="uq_coupon_usage"),
    )

    coupon = relationship("Coupon", back_populates="usages")
    user = relationship("User", back_populates="coupon_usages")
    order = relationship("Order", back_populates="coupon_usages")

class FlashSale(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "flash_sales"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    products = relationship("FlashSaleProduct", back_populates="flash_sale", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("start_date < end_date", name="flash_sale_date_valid"),
    )

class FlashSaleProduct(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "flash_sale_products"
    flash_sale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("flash_sales.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    discount_price: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    stock_limit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("flash_sale_id", "product_id", name="uq_flash_sale_product"),
    )

    flash_sale = relationship("FlashSale", back_populates="products")
    product = relationship("Product", back_populates="flash_sale_products")

class Banner(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "banners"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    link_url: Mapped[Optional[str]] = mapped_column(String(500))
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    product = relationship("Product", back_populates="banners")
    category = relationship("Category", back_populates="banners")

    __table_args__ = (
        CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR start_date < end_date",
            name="banner_date_valid",
        ),
    )

class Notification(Base, UUIDMixin):
    __tablename__ = "notifications"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    action_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="notifications")

class NotificationPreference(Base, UUIDMixin):
    __tablename__ = "notification_preferences"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    preferences: Mapped[Optional[Dict]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="notification_preference")

class ActivityLog(Base, UUIDMixin):
    __tablename__ = "activity_logs"
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[Dict]] = mapped_column(JSONB)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="activity_logs")

class AuditLog(Base, UUIDMixin):
    __tablename__ = "audit_logs"
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    old_data: Mapped[Optional[Dict]] = mapped_column(JSONB)
    new_data: Mapped[Optional[Dict]] = mapped_column(JSONB)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="audit_logs")
    


class OTP(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "otps"
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    otp: Mapped[str] = mapped_column(String(10), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_otp_email_expires", "email", "expires_at"),
    )