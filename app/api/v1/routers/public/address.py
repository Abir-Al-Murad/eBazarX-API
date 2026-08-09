from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_customer
from app.infrastructure.database.models import User
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.address import AddressCreate, AddressUpdate, AddressResponse
from app.application.services.address_service import AddressService

router = APIRouter(
    prefix="/customer/addresses",
    tags=["Customer Addresses"],
    dependencies=[Depends(get_current_customer)]
)

@router.get("/", response_model=List[AddressResponse])
async def list_addresses(
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = AddressService(uow)
    addresses = await service.get_addresses(current_user.id)
    return addresses

@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = AddressService(uow)
    try:
        address = await service.create_address(current_user.id, data)
        return address
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: UUID,
    data: AddressUpdate,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = AddressService(uow)
    try:
        address = await service.update_address(current_user.id, address_id, data)
        return address
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: UUID,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = AddressService(uow)
    try:
        await service.delete_address(current_user.id, address_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{address_id}/default", response_model=AddressResponse)
async def set_default_address(
    address_id: UUID,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = AddressService(uow)
    try:
        address = await service.set_default_address(current_user.id, address_id)
        return address
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))