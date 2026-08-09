from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from gotrue import User
from app.api.v1.schemas.user import RefreshTokenRequest, UserCreate, Token, LoginRequest
from app.application.services.auth_service import AuthService
from app.core.exceptions import BusinessError
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.dependencies.auth import get_current_user, get_uow, get_auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=dict)
async def register(user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    try:
        user = await auth_service.register_user(
            email=user_data.email,
            phone=user_data.phone,
            full_name=user_data.full_name,
            password=user_data.password
        )
        return {"message": "User registered", "user_id": str(user.id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    uow: UnitOfWork = Depends(get_uow),
):
    service = AuthService(uow)

    tokens = await service.authenticate(
        login=form_data.username,
        password=form_data.password,
    )

    return tokens


@router.post("/logout")
async def logout(
    request: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    token_record = await uow.refresh_token.get_by_token(request.refresh_token)
    if token_record and token_record.user_id == current_user.id:
        token_record.revoked = True
        await uow.commit()
    return {"message": "Logged out"}



@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        tokens = await auth_service.refresh_access_token(request.refresh_token)
        return tokens
    except BusinessError as e:
        raise HTTPException(status_code=401, detail=str(e))
# @router.post("/login/all", response_model=Token)
# async def login(creds: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
#     access, refresh = await auth_service.authenticate(creds.login, creds.password)
#     return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

# ... refresh, logout endpoints