from fastapi import APIRouter, Depends
from app.api.v1.dependencies.permissions import get_current_customer
from app.api.v1.schemas.order import OrderCreate, OrderResponse
from app.application.services.order_service import OrderService
from app.infrastructure.database.models import User
from app.api.v1.dependencies.services import get_order_service  # add this

router = APIRouter(prefix="/customer", tags=["Customer"], dependencies=[Depends(get_current_customer)])

@router.get("/me")
async def get_profile(current_user: User = Depends(get_current_customer)):
    return current_user

@router.post("/orders", response_model=OrderResponse)
async def place_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_customer),
    order_service: OrderService = Depends(get_order_service)
):
    order = await order_service.place_order(
        current_user.id,
        order_data.address_id,
        [item.dict() for item in order_data.items],
        order_data.coupon_code
    )
    return order