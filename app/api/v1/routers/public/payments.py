from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from app.api.v1.dependencies.auth import get_uow
from app.api.v1.dependencies.permissions import get_current_customer
from app.infrastructure.database.models import User
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.payment import PaymentInitiateRequest, PaymentInitiateResponse, PaymentResponse
from app.application.services.payment_service import PaymentService

router = APIRouter(
    prefix="/customer/payments",
    tags=["Customer Payments"],
    dependencies=[Depends(get_current_customer)]
)

@router.post("/initiate", response_model=PaymentInitiateResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    data: PaymentInitiateRequest,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = PaymentService(uow)
    # Verify order belongs to user
    order = await uow.orders.get(data.order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        result = await service.initiate_payment(
            order_id=data.order_id,
            gateway=data.gateway,
            success_url=data.success_url,
            cancel_url=data.cancel_url
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_status(
    payment_id: UUID,
    current_user: User = Depends(get_current_customer),
    uow: UnitOfWork = Depends(get_uow)
):
    service = PaymentService(uow)
    try:
        payment = await service.get_payment_status(payment_id)
        # Check order belongs to user
        order = await uow.orders.get(payment.order_id)
        if not order or order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        return payment
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))