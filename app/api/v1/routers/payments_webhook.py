from fastapi import APIRouter, Request, Depends, HTTPException, status
from app.api.v1.dependencies.auth import get_uow
from app.infrastructure.database.models import PaymentStatus
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.application.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payment Webhooks"])

@router.post("/sslcommerz/success", status_code=status.HTTP_200_OK)
async def sslcommerz_success(
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
):
    """
    SSLCommerz success callback (redirect or webhook).
    """
    form_data = await request.form()
    payload = dict(form_data)   # or await request.json() if they send JSON

    service = PaymentService(uow)
    try:
        payment = await service.handle_webhook(payload)
        if payment.status == PaymentStatus.PAID:
            # Redirect to frontend success page
            return {"status": "success", "message": "Payment completed", "payment_id": str(payment.id)}
        else:
            return {"status": "failed", "message": "Payment verification failed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))