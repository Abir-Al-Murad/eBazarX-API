from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models import (
    Address,
    Banner,
    Brand,
    Cart,
    CartItem,
    Category,
    Coupon,
    CouponCategory,
    CouponProduct,
    FlashSale,
    FlashSaleProduct,
    InventoryLog,
    Notification,
    NotificationPreference,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductImage,
    ProductStatistics,
    ProductVariant,
    RefreshToken,
    Review,
    ReviewImage,
    ReviewReply,
    ReviewReport,
    ReviewVote,
    Seller,
    SellerWallet,
    User,
    WalletTransaction,
    Wishlist,
    WishlistItem,
    WithdrawRequest,
)
from app.infrastructure.database.repositories import (
    address_repository,
    banner_repository,
    brand_repository,
    cart_item_repository,
    cart_repository,
    category_repository,
    coupon_category_repository,
    coupon_product_repository,
    coupon_repository,
    inventory_log_repository,
    notification_preference_repository,
    notification_repository,
    order_item_repository,
    order_repository,
    payment_repository,
    product_image_repository,
    product_repository,
    product_statistics_repository,
    product_variant_repository,
    refresh_token_repository,
    review_image_repository,
    review_reply_repository,
    review_report_repository,
    review_repository,
    review_vote_repository,
    seller_repository,
    user_repository,
    wallet_repository,
    wallet_transaction_repository,
    wishlist_repository,
    withdraw_request_repository,
)
from app.infrastructure.database.repositories.flash_sale_product_repository import (
    FlashSaleProductRepository,
)
from app.infrastructure.database.repositories.flash_sale_repository import (
    FlashSaleRepository,
)


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session


        self.refresh_token = refresh_token_repository.RefreshTokenRepository(RefreshToken, session)
        # Auth & Users
        self.users = user_repository.UserRepository(User, session)
        self.sellers = seller_repository.SellerRepository(Seller, session)

        # Catalog
        self.products = product_repository.ProductRepository(Product, session)
        self.variants = product_variant_repository.ProductVariantRepository(
            ProductVariant, session
        )
        self.categories = category_repository.CategoryRepository(Category, session)
        self.brands = brand_repository.BrandRepository(Brand, session)
        self.product_images = product_image_repository.ProductImageRepository(
            ProductImage, session
        )

        # Orders
        self.orders = order_repository.OrderRepository(Order, session)
        self.order_items = order_item_repository.OrderItemRepository(OrderItem, session)

        # Payments & Wallet
        self.payments = payment_repository.PaymentRepository(Payment, session)
        self.refunds = payment_repository.PaymentRepository(Payment, session)  # reuse
        self.wallets = wallet_repository.WalletRepository(SellerWallet, session)
        self.wallet_transactions = wallet_transaction_repository.WalletTransactionRepository(
            WalletTransaction, session
        )
        self.withdraw_requests = withdraw_request_repository.WithdrawRequestRepository(
            WithdrawRequest, session
        )

        # Coupons
        self.coupons = coupon_repository.CouponRepository(Coupon, session)
        self.coupon_products = coupon_product_repository.CouponProductRepository(
            CouponProduct, session
        )
        self.coupon_categories = coupon_category_repository.CouponCategoryRepository(
            CouponCategory, session
        )

        # Cart & Wishlist
        self.carts = cart_repository.CartRepository(Cart, session)
        self.cart_items = cart_item_repository.CartItemRepository(CartItem, session)
        self.wishlists = wishlist_repository.WishlistRepository(Wishlist, session)
        self.wishlist_items = wishlist_repository.WishlistItemRepository(
            WishlistItem, session
        )

        # Addresses
        self.addresses = address_repository.AddressRepository(Address, session)

        # Inventory
        self.inventory_logs = inventory_log_repository.InventoryLogRepository(
            InventoryLog, session
        )

        # Marketing
        self.flash_sales = FlashSaleRepository(FlashSale, session)
        self.flash_sale_products = FlashSaleProductRepository(
            FlashSaleProduct, session
        )
        self.banners = banner_repository.BannerRepository(Banner, session)

        # Notifications
        self.notifications = notification_repository.NotificationRepository(
            Notification, session
        )
        self.notification_preferences = (
            notification_preference_repository.NotificationPreferenceRepository(
                NotificationPreference, session
            )
        )

        # Reviews (full module)
        self.reviews = review_repository.ReviewRepository(Review, session)
        self.review_images = review_image_repository.ReviewImageRepository(
            ReviewImage, session
        )
        self.review_votes = review_vote_repository.ReviewVoteRepository(
            ReviewVote, session
        )
        self.review_reports = review_report_repository.ReviewReportRepository(
            ReviewReport, session
        )
        self.review_replies = review_reply_repository.ReviewReplyRepository(
            ReviewReply, session
        )
        
        self.product_statistics = product_statistics_repository.ProductStatisticsRepository(
            ProductStatistics, session
        )

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    async def refresh(self, instance):
        await self.session.refresh(instance)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        await self.session.close()