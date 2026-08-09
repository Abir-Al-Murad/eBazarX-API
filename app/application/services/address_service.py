from uuid import UUID
from typing import Optional
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.core.exceptions import BusinessError
from app.api.v1.schemas.address import AddressCreate, AddressUpdate

class AddressService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_address(self, user_id: UUID, data: AddressCreate):
        # If this is the first address, force it as default
        count = await self.uow.addresses.count_by_user(user_id)
        is_default = data.is_default if count > 0 else True

        # If setting as default, clear other defaults
        if is_default:
            await self.uow.addresses.set_default(None, user_id)  # We need a method to clear defaults without setting a new one

        address = await self.uow.addresses.create(
            user_id=user_id,
            full_name=data.full_name,
            phone=data.phone,
            division=data.division,
            district=data.district,
            upazila=data.upazila,
            area=data.area,
            address_line=data.address_line,
            postal_code=data.postal_code,
            label=data.label,
            is_default=is_default
        )
        await self.uow.commit()
        await self.uow.refresh(address)
        return address

    async def update_address(self, user_id: UUID, address_id: UUID, data: AddressUpdate):
        address = await self.uow.addresses.get(address_id)
        if not address or address.user_id != user_id:
            raise BusinessError("Address not found")

        # Handle default flag
        if data.is_default is True:
            # Clear other defaults for this user
            await self.uow.addresses.set_default(address_id, user_id)
            address.is_default = True
        elif data.is_default is False:
            # If trying to unset default, check if there are other addresses
            count = await self.uow.addresses.count_by_user(user_id)
            if count <= 1:
                raise BusinessError("Cannot unset default; no other addresses exist")
            address.is_default = False

        # Apply updates
        update_data = data.model_dump(exclude_unset=True, exclude={'is_default'})
        for key, value in update_data.items():
            setattr(address, key, value)

        await self.uow.commit()
        await self.uow.refresh(address)
        return address

    async def delete_address(self, user_id: UUID, address_id: UUID):
        address = await self.uow.addresses.get(address_id)
        if not address or address.user_id != user_id:
            raise BusinessError("Address not found")

        # If this is the default address and there are others, set another as default
        if address.is_default:
            other_addresses = await self.uow.addresses.get_by_user(user_id)
            if len(other_addresses) > 1:
                # Find the first other address and set it as default
                for other in other_addresses:
                    if other.id != address_id:
                        await self.uow.addresses.set_default(other.id, user_id)
                        break

        # Soft delete
        from datetime import datetime, timezone
        address.deleted_at = datetime.now(timezone.utc)
        await self.uow.commit()

    async def set_default_address(self, user_id: UUID, address_id: UUID):
        address = await self.uow.addresses.get(address_id)
        if not address or address.user_id != user_id:
            raise BusinessError("Address not found")
        await self.uow.addresses.set_default(address_id, user_id)
        await self.uow.commit()
        await self.uow.refresh(address)
        return address

    async def get_addresses(self, user_id: UUID):
        return await self.uow.addresses.get_by_user(user_id)

    async def get_default_address(self, user_id: UUID):
        return await self.uow.addresses.get_default(user_id)