from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_seller
from app.infrastructure.database.models import Seller
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.wallet import WalletResponse, WalletTransactionResponse, WithdrawalRequestCreate, WithdrawalRequestResponse
from app.application.services.wallet_service import WalletService

router = APIRouter(
    prefix="/seller/wallet",
    tags=["Seller Wallet"],
    dependencies=[Depends(get_current_seller)]
)

@router.get("/", response_model=WalletResponse)
async def get_wallet(
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    service = WalletService(uow)
    wallet = await service.get_wallet(current_seller.id)
    return wallet

@router.get("/transactions", response_model=List[WalletTransactionResponse])
async def get_transactions(
    skip: int = 0,
    limit: int = 50,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    service = WalletService(uow)
    transactions = await service.get_transactions(current_seller.id, skip, limit)
    return transactions

@router.post("/withdraw", response_model=WithdrawalRequestResponse, status_code=status.HTTP_201_CREATED)
async def request_withdrawal(
    data: WithdrawalRequestCreate,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    service = WalletService(uow)
    try:
        request = await service.request_withdrawal(current_seller.id, data)
        return request
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/withdrawals", response_model=List[WithdrawalRequestResponse])
async def list_withdrawals(
    skip: int = 0,
    limit: int = 20,
    current_seller: Seller = Depends(get_current_seller),
    uow: UnitOfWork = Depends(get_uow)
):
    requests = await uow.withdraw_requests.get_by_seller(current_seller.id, skip, limit)
    return requests