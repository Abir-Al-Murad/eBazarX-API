from decimal import Decimal
from uuid import UUID
from typing import Optional, List, Dict, Any
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError, InsufficientStockError


class CartService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_or_create_cart(self, user_id: UUID):
        """Get existing cart or create a new one."""
        cart = await self.uow.carts.get_by_user(user_id)
        if not cart:
            cart = await self.uow.carts.create(user_id=user_id)
            await self.uow.commit()
        return cart

    async def add_item(self, user_id: UUID, variant_id: UUID, quantity: int):
        """Add an item to the user's cart."""
        cart = await self.get_or_create_cart(user_id)

        # Check variant and stock
        variant = await self.uow.variants.get(variant_id)
        if not variant:
            raise BusinessError("Variant not found")
        available = variant.stock - variant.reserved_stock
        if available < quantity:
            raise InsufficientStockError(f"Not enough stock. Available: {available}, Requested: {quantity}")

        # Check if item already in cart
        existing = await self.uow.cart_items.get_by_cart_and_variant(cart.id, variant_id)
        if existing:
            existing.quantity += quantity
        else:
            await self.uow.cart_items.create(
                cart_id=cart.id,
                variant_id=variant_id,
                quantity=quantity,
                product_id=variant.product_id,
            )
        await self.uow.commit()

    async def update_item(self, user_id: UUID, item_id: UUID, quantity: int):
        """Update quantity of a cart item."""
        item = await self.uow.cart_items.get(item_id)
        if not item:
            raise BusinessError("Item not found")
        cart = await self.uow.carts.get(item.cart_id)
        if not cart or cart.user_id != user_id:
            raise BusinessError("Item does not belong to user")

        if quantity <= 0:
            await self.uow.cart_items.delete(item.id)
        else:
            item.quantity = quantity
        await self.uow.commit()

    async def remove_item(self, user_id: UUID, item_id: UUID):
        """Remove an item from the cart."""
        item = await self.uow.cart_items.get(item_id)
        if not item:
            raise BusinessError("Item not found")
        cart = await self.uow.carts.get(item.cart_id)
        if not cart or cart.user_id != user_id:
            raise BusinessError("Item does not belong to user")
        await self.uow.cart_items.delete(item.id)
        await self.uow.commit()

    async def get_cart(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get the user's cart with enriched item details.
        Returns a dict with 'id', 'items', 'subtotal', 'total_items'.
        If no cart exists, returns id=None and empty items.
        """
        cart = await self.uow.carts.get_by_user(user_id)
        if not cart:
            return {
                "id": None,
                "items": [],
                "subtotal": Decimal(0),
                "total_items": 0,
            }

        items = await self.uow.cart_items.get_by_cart(cart.id)
        enriched = []
        subtotal = Decimal(0)

        for item in items:
            variant = await self.uow.variants.get(item.variant_id)
            if not variant:
                continue
            product = await self.uow.products.get(variant.product_id)
            if not product:
                continue

            price = variant.price_override or product.price
            total = price * item.quantity
            subtotal += total

            product_image = None
            if product.images and len(product.images) > 0:
                product_image = product.images[0].url

            enriched.append({
                "id": item.id,
                "variant_id": item.variant_id,
                "product_id": product.id,
                "product_name": product.name,
                "price": price,
                "quantity": item.quantity,
                "total": total,
                "variant_attributes": variant.attributes,
                "product_image": product_image,
            })

        return {
            "id": cart.id,
            "items": enriched,
            "subtotal": subtotal,
            "total_items": sum(item.quantity for item in items),
        }

    async def clear_cart(self, user_id: UUID):
        """Clear all items from the user's cart."""
        cart = await self.uow.carts.get_by_user(user_id)
        if cart:
            await self.uow.carts.clear_cart(cart.id)
            await self.uow.commit()