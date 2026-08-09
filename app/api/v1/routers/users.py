from fastapi import APIRouter, Depends
from app.api.v1.dependencies.auth import get_current_user, get_uow
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.infrastructure.database.models import User
from app.api.v1.schemas.user import AuthenticatedUserProfileResponse
from app.application.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=AuthenticatedUserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    service = UserService(uow)
    profile_data = await service.get_authenticated_profile(current_user.id)
    return profile_data