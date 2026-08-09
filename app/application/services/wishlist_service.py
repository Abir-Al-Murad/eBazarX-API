from uuid import UUID
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError

class WishlistService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_or_create_wishlist(self, user_id: UUID):
        wishlist = await self.uow.wishlists.get_by_user(user_id)
        if not wishlist:
            wishlist = await self.uow.wishlists.create(user_id=user_id)
            await self.uow.commit()
            await self.uow.refresh(wishlist)
        return wishlist

    async def add_item(self, user_id: UUID, variant_id: UUID):
        # Fetch variant to get product_id
        variant = await self.uow.variants.get(variant_id)
        if not variant:
            raise BusinessError("Variant not found")
        
        wishlist = await self.get_or_create_wishlist(user_id)
        
        # Check if already in wishlist
        existing = await self.uow.wishlist_items.get_by_wishlist_and_variant(
            wishlist.id, variant_id
        )
        if existing:
            raise BusinessError("Item already in wishlist")
        
        await self.uow.wishlist_items.create(
            wishlist_id=wishlist.id,
            variant_id=variant_id,
            product_id=variant.product_id  # Now variant is defined
        )
        await self.uow.commit()

    async def remove_item(self, user_id: UUID, item_id: UUID):
        item = await self.uow.wishlist_items.get(item_id)
        if not item:
            raise BusinessError("Item not found")
        
        wishlist = await self.uow.wishlists.get(item.wishlist_id)
        if not wishlist or wishlist.user_id != user_id:
            raise BusinessError("Item does not belong to user")
        
        await self.uow.wishlist_items.delete(item.id)
        await self.uow.commit()

    async def get_wishlist(self, user_id: UUID):
        wishlist = await self.uow.wishlists.get_by_user(user_id)
        if not wishlist:
            return {"id": None, "items": [], "total_items": 0}
        
        items = await self.uow.wishlist_items.get_by_wishlist(wishlist.id)
        # Enrich items with product/variant details
        enriched = []
        for item in items:
            variant = await self.uow.variants.get(item.variant_id)
            if not variant:
                continue
            product = await self.uow.products.get(variant.product_id)
            if not product:
                continue
            enriched.append({
                "id": item.id,
                "variant_id": item.variant_id,
                "product_id": product.id,
                "product_name": product.name,
                "price": variant.price_override or product.price,
                "variant_attributes": variant.attributes,
                "product_image": product.images[0].url if product.images and len(product.images) > 0 else None,
                "added_at": item.created_at
            })
        
        return {
            "id": wishlist.id,
            "items": enriched,
            "total_items": len(enriched)
        }

    async def clear_wishlist(self, user_id: UUID):
        wishlist = await self.uow.wishlists.get_by_user(user_id)
        if wishlist:
            # Delete all items
            items = await self.uow.wishlist_items.get_by_wishlist(wishlist.id)
            for item in items:
                await self.uow.wishlist_items.delete(item.id)
            await self.uow.commit()