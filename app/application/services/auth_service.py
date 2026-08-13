import re
import random
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from app.core.security import (
    decode_token,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.core.exceptions import BusinessError, ForbiddenError, UnauthorizedError
from app.core.config import settings
from app.core.cache.redis_service import redis_service
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.infrastructure.database.models import User
from app.core.email import email_service


class AuthService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.otp_expiry_seconds = 300  # 5 minutes
        self.otp_length = 6

    # ---------- OTP Generation ----------
    def _generate_otp(self) -> str:
        """Generate a 6-digit OTP."""
        return ''.join(str(random.randint(0, 9)) for _ in range(self.otp_length))

    async def _store_otp(self, identifier: str, otp: str) -> None:
        """Store OTP in Redis with expiry."""
        key = f"otp:{identifier}"
        await redis_service.set(key, otp, ttl=self.otp_expiry_seconds)

    async def _get_otp(self, identifier: str) -> Optional[str]:
        """Retrieve OTP from Redis."""
        return await redis_service.get(f"otp:{identifier}")

    async def _delete_otp(self, identifier: str) -> None:
        """Delete OTP from Redis."""
        await redis_service.delete(f"otp:{identifier}")

    async def _store_verified_flag(self, identifier: str) -> None:
        """Mark identifier as verified (OTP verified)."""
        key = f"verified:{identifier}"
        await redis_service.set(key, "true", ttl=600)  # 10 minutes to complete registration

    async def _is_verified(self, identifier: str) -> bool:
        """Check if identifier is verified."""
        return await redis_service.exists(f"verified:{identifier}")

    async def _clear_verified_flag(self, identifier: str) -> None:
        """Clear verified flag."""
        await redis_service.delete(f"verified:{identifier}")

    # ---------- Request OTP ----------
    async def request_otp(self, identifier: str) -> dict:
        """
        Request OTP for registration.
        identifier can be email or phone.
        """
        # Check if identifier already registered
        existing_email = await self.uow.users.get_by_email(identifier)
        if existing_email:
            raise BusinessError("Email already registered", status_code=409)
        existing_phone = await self.uow.users.get_by_phone(identifier)
        if existing_phone:
            raise BusinessError("Phone already registered", status_code=409)

        # Generate and store OTP
        otp = self._generate_otp()
        await self._store_otp(identifier, otp)

        # Send OTP via email or SMS based on identifier format
        if "@" in identifier:  # Email
            try:
                email_service.send_otp_email(identifier, otp)
            except Exception as e:
                print(f"Failed to send email: {e}. OTP: {otp}")
        else:  # Phone
            # TODO: Integrate SMS gateway (e.g., Twilio, bKash)
            print(f"SMS OTP for {identifier}: {otp}")

        return {
            "message": "OTP sent successfully",
            "identifier": identifier,
            "expires_in": self.otp_expiry_seconds,
        }

    # ---------- Resend OTP ----------
    async def resend_otp(self, identifier: str) -> dict:
        """Resend OTP to identifier (email or phone)."""
        # Check if identifier is already registered (can't resend if already registered)
        existing_email = await self.uow.users.get_by_email(identifier)
        if existing_email:
            raise BusinessError("Email already registered", status_code=409)
        existing_phone = await self.uow.users.get_by_phone(identifier)
        if existing_phone:
            raise BusinessError("Phone already registered", status_code=409)

        # Generate and store new OTP
        otp = self._generate_otp()
        await self._store_otp(identifier, otp)

        # Send OTP
        if "@" in identifier:
            try:
                email_service.send_otp_email(identifier, otp)
            except Exception as e:
                print(f"Failed to send email: {e}. OTP: {otp}")
        else:
            print(f"SMS OTP for {identifier}: {otp}")

        return {
            "message": "OTP resent successfully",
            "identifier": identifier,
            "expires_in": self.otp_expiry_seconds,
        }

    # ---------- Verify OTP ----------
    async def verify_otp(self, identifier: str, otp: str) -> dict:
        """
        Verify OTP and mark identifier as verified.
        """
        stored_otp = await self._get_otp(identifier)
        if not stored_otp:
            raise BusinessError("OTP expired or not found", status_code=400)
        if stored_otp != otp:
            raise BusinessError("Invalid OTP", status_code=400)

        # Delete OTP and mark as verified
        await self._delete_otp(identifier)
        await self._store_verified_flag(identifier)

        return {
            "message": "OTP verified successfully",
            "identifier": identifier,
            "verified": True,
        }

    # ---------- Password strength ----------
    def _validate_password_strength(self, password: str) -> Optional[str]:
        min_len = getattr(settings, "PASSWORD_MIN_LENGTH", 8)
        if len(password) < min_len:
            return f"Password must be at least {min_len} characters long."

        if getattr(settings, "PASSWORD_REQUIRE_UPPERCASE", True) and not re.search(r"[A-Z]", password):
            return "Password must contain at least one uppercase letter."

        if getattr(settings, "PASSWORD_REQUIRE_LOWERCASE", True) and not re.search(r"[a-z]", password):
            return "Password must contain at least one lowercase letter."

        if getattr(settings, "PASSWORD_REQUIRE_DIGIT", True) and not re.search(r"\d", password):
            return "Password must contain at least one digit."

        if getattr(settings, "PASSWORD_REQUIRE_SPECIAL", True) and not re.search(
            r"[!@#$%^&*(),.?\":{}|<>]", password
        ):
            return "Password must contain at least one special character (e.g., !@#$%^&*)."

        if getattr(settings, "PASSWORD_DISALLOW_COMMON", False):
            common_passwords = {"password", "12345678", "qwerty", "password123"}
            if password.lower() in common_passwords:
                return "Password is too common. Please choose a more secure password."

        return None

    # ---------- Registration (with OTP verification) ----------
    async def register_user(
        self,
        email: str,
        phone: str,
        full_name: str,
        password: str,
        profile_image: Optional[str] = None,
    ) -> User:
        """
        Register a new user. Requires OTP verification for email or phone.
        """
        # Check if user already exists
        existing_email = await self.uow.users.get_by_email(email)
        if existing_email:
            raise BusinessError("Email already registered", status_code=409)

        existing_phone = await self.uow.users.get_by_phone(phone)
        if existing_phone:
            raise BusinessError("Phone already registered", status_code=409)

        # Check OTP verification (at least one identifier must be verified)
        email_verified = await self._is_verified(email)
        phone_verified = await self._is_verified(phone)
        if not email_verified and not phone_verified:
            raise BusinessError(
                "OTP verification required. Please verify your email or phone.",
                status_code=400
            )

        # Validate password strength
        password_error = self._validate_password_strength(password)
        if password_error:
            raise BusinessError(password_error, status_code=400)

        # Create user
        user = await self.uow.users.create(
            email=email,
            phone=phone,
            full_name=full_name,
            password_hash=get_password_hash(password),
            profile_image=profile_image,
            is_active=True,
            is_verified=True,  # Verified because OTP was confirmed
        )

        await self.uow.commit()

        # Clear verification flags after successful registration
        await self._clear_verified_flag(email)
        await self._clear_verified_flag(phone)

        return user

    # ---------- Authentication ----------
    async def authenticate(self, login: str, password: str) -> dict:
        user = await self.uow.users.get_by_email(login)
        if user is None:
            user = await self.uow.users.get_by_phone(login)
        if user is None:
            raise ForbiddenError("User not found")
        if not verify_password(password, user.password_hash):
            raise ForbiddenError("Password does not match")
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")

        user.last_login = datetime.now(timezone.utc)
        await self.uow.commit()

        access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.uow.refresh_token.create(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
            revoked=False,
        )
        await self.uow.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    # ---------- Refresh ----------
    async def refresh_access_token(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload:
            raise BusinessError("Invalid refresh token")
        if payload.get("type") != "refresh":
            raise BusinessError("Invalid token type")

        exp = payload.get("exp")
        if exp:
            exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
            if exp_dt < datetime.now(timezone.utc):
                raise BusinessError("Refresh token expired")

        user_id = payload.get("sub")
        if not user_id:
            raise BusinessError("Invalid token payload")

        token_record = await self.uow.refresh_token.get_by_token(refresh_token)
        if not token_record:
            raise BusinessError("Token not found")
        if token_record.revoked:
            raise BusinessError("Token revoked")

        token_record.revoked = True
        await self.uow.commit()

        new_access = create_access_token({"sub": str(user_id), "role": payload.get("role")})
        new_refresh = create_refresh_token({"sub": str(user_id), "role": payload.get("role")})

        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.uow.refresh_token.create(
            user_id=user_id,
            token=new_refresh,
            expires_at=expires_at,
            revoked=False,
        )
        await self.uow.commit()

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }