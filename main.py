from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import BusinessError
from app.core.middleware.logging import LoggingMiddleware
from app.api.v1.routers import reviews as customer_reviews, upload
from app.api.v1.routers.seller import reviews as seller_reviews
from app.api.v1.routers.public import reviews as public_reviews
from app.api.v1.routers.admin import reviews as admin_reviews
from app.api.v1.routers.seller import seller as seller_router
from app.api.v1.routers.admin import sellers as admin_sellers_router
from app.api.v1.routers import users as public_users
from app.api.v1.routers import payments_webhook

# ---------------- Public ----------------
from app.api.v1.routers.public import (
    auth,
    public,
    customer,
    categories,
    products as public_products,
    cart,
    orders as customer_orders,
    address,
    wishlist,
    payments,
    webhooks,
    flash_sales,
    coupons,
    banners,
    notifications,
)

# ---------------- Seller ----------------
from app.api.v1.routers.seller import (
    seller,
    dashboard as seller_dashboard,
    products as seller_products,
    orders as seller_orders,
    coupons as seller_coupons,
    wallet as seller_wallet,
)

# ---------------- Admin ----------------
from app.api.v1.routers.admin import (
    admin,
    dashboard as admin_dashboard,
    products as admin_products,
    categories as admin_categories,
    orders as admin_orders,
    coupons as admin_coupons,
    flash_sales as admin_flash_sales,
    banners as admin_banners,
    wallet as admin_wallet,
    withdrawals as admin_withdrawals,
    notifications as admin_notifications,
)


# =============================================================================
# App
# =============================================================================

app = FastAPI(
    title="eBazar API",
    version="1.0.0",
)


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(BusinessError)
async def business_exception_handler(
    request: Request,
    exc: BusinessError,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if errors:
        err = errors[0]
        # Filter out 'body' from location parts to avoid 'body.password'
        loc_parts = [str(loc) for loc in err['loc'] if str(loc) != 'body']
        field = ".".join(loc_parts) if loc_parts else "Field"
        msg = err['msg']
        msg = msg[0].upper() + msg[1:] if msg else msg
        message = f"{field}: {msg}"
    else:
        message = "Validation error"
    return JSONResponse(status_code=422, content={"message": message})

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
        },
    )


# =============================================================================
# Middleware
# =============================================================================

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# API Prefix
# =============================================================================

API_PREFIX = "/api/v1"


# =============================================================================
# Authentication
# =============================================================================

app.include_router(auth.router, prefix=API_PREFIX)



# =============================================================================
# Public APIs
# =============================================================================

app.include_router(public_users.router, prefix=API_PREFIX)
app.include_router(public.router, prefix=API_PREFIX)
app.include_router(categories.router, prefix=API_PREFIX)
app.include_router(public_products.router, prefix=API_PREFIX)
app.include_router(public_reviews.router, prefix=API_PREFIX)
app.include_router(customer_reviews.router, prefix=API_PREFIX)
app.include_router(cart.router, prefix=API_PREFIX)
app.include_router(customer.router, prefix=API_PREFIX)
app.include_router(customer_orders.router, prefix=API_PREFIX)
app.include_router(address.router, prefix=API_PREFIX)
app.include_router(wishlist.router, prefix=API_PREFIX)
app.include_router(payments.router, prefix=API_PREFIX)
app.include_router(webhooks.router, prefix=API_PREFIX)
app.include_router(flash_sales.router, prefix=API_PREFIX)
app.include_router(coupons.router, prefix=API_PREFIX)
app.include_router(banners.router, prefix=API_PREFIX)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(upload.router, prefix=API_PREFIX)

app.include_router(payments_webhook.router, prefix=API_PREFIX)
from app.api.v1.routers.seller import seller as seller_router

app.include_router(seller_router.router, prefix=API_PREFIX)
# app.include_router(pub, prefix=API_PREFIX)



# =============================================================================
# Seller APIs
# =============================================================================

app.include_router(seller.router, prefix=API_PREFIX)
app.include_router(seller_dashboard.router, prefix=API_PREFIX)
app.include_router(seller_products.router, prefix=API_PREFIX)
app.include_router(seller_reviews.router, prefix=API_PREFIX)
app.include_router(seller_orders.router, prefix=API_PREFIX)
app.include_router(seller_coupons.router, prefix=API_PREFIX)
app.include_router(seller_wallet.router, prefix=API_PREFIX)
app.include_router(seller_router.router, prefix=API_PREFIX)
app.include_router(seller_router.apply_router, prefix=API_PREFIX)


# =============================================================================
# Admin APIs
# =============================================================================

app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(admin_dashboard.router, prefix=API_PREFIX)
app.include_router(admin_categories.router, prefix=API_PREFIX)
app.include_router(admin_products.router, prefix=API_PREFIX)
app.include_router(admin_reviews.router, prefix=API_PREFIX)
app.include_router(admin_orders.router, prefix=API_PREFIX)
app.include_router(admin_coupons.router, prefix=API_PREFIX)
app.include_router(admin_flash_sales.router, prefix=API_PREFIX)
app.include_router(admin_banners.router, prefix=API_PREFIX)
app.include_router(admin_wallet.router, prefix=API_PREFIX)
app.include_router(admin_withdrawals.router, prefix=API_PREFIX)
app.include_router(admin_notifications.router, prefix=API_PREFIX)
app.include_router(admin_sellers_router.router, prefix=API_PREFIX)

# =============================================================================
# Health Check
# =============================================================================

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "success": True,
        "status": "ok",
        "version": app.version,
    }