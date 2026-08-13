from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.v1.schemas.user import (
    RefreshTokenRequest,
    UserCreate,
    Token,
    OTPVerifyRequest,
    OTPResendRequest,
    RegistrationOTPResponse,
    UserRegisterWithOTP,
)
from app.application.services.auth_service import AuthService
from app.core.exceptions import BusinessError
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.api.v1.dependencies.auth import get_current_user, get_uow, get_auth_service
from app.infrastructure.database.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ============================================================
# NEW Registration OTP Flow (Full Data First)
# ============================================================

@router.post("/request-registration-otp", response_model=RegistrationOTPResponse)
async def request_registration_otp(
    data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Step 1: Validate full registration data and send OTP to email.
    """
    try:
        result = await auth_service.request_registration_otp(data.model_dump())
        return result
    except BusinessError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/register")
async def register_with_otp(
    data: UserRegisterWithOTP,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Step 2: Verify OTP and create the user account.
    """
    try:
        user = await auth_service.register_with_otp(data.model_dump())
        return {"message": "User registered successfully", "user_id": str(user.id)}
    except BusinessError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================
# DEPRECATED OTP & Registration Endpoints (kept for backward compatibility)
# ============================================================

@router.post("/request-otp")
async def request_otp_deprecated(
    data: OTPResendRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    DEPRECATED: Use /request-registration-otp instead.
    """
    try:
        result = await auth_service.request_otp(data.email)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-otp")
async def verify_otp_deprecated(
    data: OTPVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    DEPRECATED: Use /register (with otp) instead.
    """
    try:
        result = await auth_service.verify_otp(data.email, data.otp)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/resend-otp")
async def resend_otp_deprecated(
    data: OTPResendRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    DEPRECATED: Use /request-registration-otp instead.
    """
    try:
        result = await auth_service.resend_otp(data.email)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/register-old")
async def register_user_old(
    data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    DEPRECATED: Use /register with OTP instead.
    """
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

# ============================================================
# Authentication (unchanged)
# ============================================================

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
    uow: UnitOfWork = Depends(get_uow),
):
    token_record = await uow.refresh_token.get_by_token(request.refresh_token)
    if token_record and token_record.user_id == current_user.id:
        token_record.revoked = True
        await uow.commit()
    return {"message": "Logged out"}

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