from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.v1.schemas.user import RefreshTokenRequest, UserCreate, Token, OTPVerifyRequest, OTPResendRequest
from app.application.services.auth_service import AuthService
from app.core.exceptions import BusinessError
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.dependencies.auth import get_current_user, get_uow, get_auth_service
from app.infrastructure.database.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- OTP ---

@router.post("/request-otp")
async def request_otp(
    data: OTPResendRequest,  # using email field
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.request_otp(data.email)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-otp")
async def verify_otp(
    data: OTPVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.verify_otp(data.email, data.otp)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/resend-otp")
async def resend_otp(
    data: OTPResendRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.resend_otp(data.email)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Registration (after OTP verification) ---

@router.post("/register")
async def register_user(
    data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        user = await auth_service.register_user(
            email=data.email,
            phone=data.phone,
            full_name=data.full_name,
            password=data.password,
            profile_image=data.profile_image,
        )
        return {"message": "User registered successfully", "user_id": str(user.id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Login ---

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

# --- Logout ---

@router.post("/logout")
async def logout(
    request: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    token_record = await uow.refresh_token.get_by_token(request.refresh_token)
    if token_record and token_record.user_id == current_user.id:
        token_record.revoked = True
        await uow.commit()
    return {"message": "Logged out"}

# --- Refresh ---

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        tokens = await auth_service.refresh_access_token(request.refresh_token)
        return tokens
    except BusinessError as e:
        raise HTTPException(status_code=401, detail=str(e))