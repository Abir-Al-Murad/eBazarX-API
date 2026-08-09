from fastapi import Depends
from app.infrastructure.database.repositories.order_item_repository import OrderItemRepository
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.dependencies.auth import get_uow
from app.application.services import (
    order_service, product_service, payment_service, wallet_service, inventory_service, pricing_service, auth_service

)
from app.infrastructure.messaging.event_bus import CeleryEventBus
from app.infrastructure.storage.supabase import SupabaseStorage
# from app.infrastructure.payment.gateway import PaymentGatewayService  # to be created


def get_event_bus() -> CeleryEventBus:
    return CeleryEventBus()

def get_storage() -> SupabaseStorage:
    return SupabaseStorage()

def get_auth_service(uow: UnitOfWork = Depends(get_uow)) -> auth_service.AuthService:
    return auth_service.AuthService(uow)

def get_product_service(uow: UnitOfWork = Depends(get_uow), event_bus: CeleryEventBus = Depends(get_event_bus)) -> product_service.ProductService:
    return product_service.ProductService(uow, event_bus)

def get_inventory_service(uow: UnitOfWork = Depends(get_uow)) -> inventory_service.InventoryService:
    return inventory_service.InventoryService(uow)

def get_pricing_service() -> pricing_service.PricingService:
    return pricing_service.PricingService()

def get_order_service(
    uow: UnitOfWork = Depends(get_uow),
    event_bus: CeleryEventBus = Depends(get_event_bus),
    inventory_service: inventory_service.InventoryService = Depends(get_inventory_service),
    pricing_service: pricing_service.PricingService = Depends(get_pricing_service)
) -> order_service.OrderService:
    return order_service.OrderService(uow, event_bus, inventory_service, pricing_service)


def get_order_item_repo(uow: UnitOfWork = Depends(get_uow)) -> OrderItemRepository:
    return uow.order_items 
# Similarly for PaymentService, WalletService, etc.