from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.dependencies.auth import get_uow
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.schemas.payment import PaymentWebhookPayload
from app.application.services.payment_service import PaymentService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/payment")
async def payment_webhook(
    data: PaymentWebhookPayload,
    uow: UnitOfWork = Depends(get_uow)
):
    service = PaymentService(uow)
    try:
        await service.handle_webhook(
            order_id=data.order_id,
            transaction_id=data.transaction_id,
            status=data.status,
            gateway_data=data.gateway_data
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))