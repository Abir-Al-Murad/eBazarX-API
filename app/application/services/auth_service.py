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
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.infrastructure.database.models import User
from app.core.email import email_service


class AuthService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.otp_expiry_seconds = 300  # 5 minutes
        self.otp_length = 6

    # ============================================================
    # OTP Helpers
    # ============================================================

    def _generate_otp(self) -> str:
        """Generate a 6-digit OTP."""
        return ''.join(str(random.randint(0, 9)) for _ in range(self.otp_length))

    def _validate_password_strength(self, password: str) -> Optional[str]:
        """Validate password strength; returns error message or None."""
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

    def _validate_registration_data(
        self,
        full_name: str,
        email: str,
        phone: str,
        password: str,
    ) -> None:
        """Validate all registration fields; raises BusinessError if any is invalid."""
        if not full_name or len(full_name.strip()) < 2:
            raise BusinessError("Full name must be at least 2 characters.", status_code=400)

        # Email format validation (simple)
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise BusinessError("Invalid email format.", status_code=400)

        # Phone validation (basic – can be improved)
        if not phone or len(phone) < 10:
            raise BusinessError("Invalid phone number.", status_code=400)

        # Password strength
        password_error = self._validate_password_strength(password)
        if password_error:
            raise BusinessError(password_error, status_code=400)

    # ============================================================
    # NEW Registration OTP Flow (Full Data First)
    # ============================================================

    async def request_registration_otp(self, user_data: dict) -> dict:
        """
        Step 1: Validate all registration data, then send OTP via email.
        Raises HTTP 502 if the email service fails.
        """
        full_name = user_data.get("full_name")
        email = user_data.get("email")
        phone = user_data.get("phone")
        password = user_data.get("password")

        # Ensure required fields are present and non-null
        if not all([full_name, email, phone, password]):
            raise BusinessError("Missing required fields: full_name, email, phone, password", status_code=400)

        # Type narrowing: assert they are str
        assert isinstance(full_name, str)
        assert isinstance(email, str)
        assert isinstance(phone, str)
        assert isinstance(password, str)

        # Validate all fields
        self._validate_registration_data(full_name, email, phone, password)

        # Check duplicates
        existing_email = await self.uow.users.get_by_email(email)
        if existing_email:
            raise BusinessError("Email already registered", status_code=409)
        existing_phone = await self.uow.users.get_by_phone(phone)
        if existing_phone:
            raise BusinessError("Phone already registered", status_code=409)

        # Generate OTP and store in PostgreSQL
        otp = self._generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.otp_expiry_seconds)
        otp_record = await self.uow.otps.create_otp(email, otp, expires_at)
        await self.uow.commit()

        # Send OTP via email (async)
        success = await email_service.send_otp_email(email, otp)
        if not success:
            # Mark the OTP as used so it cannot be verified
            await self.uow.otps.mark_used(otp_record.id)
            await self.uow.commit()
            # Raise an error so the API does not return 200 OK
            raise BusinessError(
                "Failed to send OTP email. Please try again later.",
                status_code=502  # Bad Gateway
            )

        return {
            "message": "OTP sent successfully",
            "email": email,
            "expires_in": self.otp_expiry_seconds,
        }

    async def register_with_otp(self, user_data: dict) -> User:
        """
        Step 2: Verify OTP and create the user.
        """
        full_name = user_data.get("full_name")
        email = user_data.get("email")
        phone = user_data.get("phone")
        password = user_data.get("password")
        profile_image = user_data.get("profile_image")
        otp = user_data.get("otp")

        # Ensure required fields are present
        if not all([full_name, email, phone, password, otp]):
            raise BusinessError("Missing required fields", status_code=400)

        # Type narrowing: assert they are str
        assert isinstance(full_name, str)
        assert isinstance(email, str)
        assert isinstance(phone, str)
        assert isinstance(password, str)
        assert isinstance(otp, str)

        # Re-validate all fields (in case they changed)
        self._validate_registration_data(full_name, email, phone, password)

        # Check duplicates again
        existing_email = await self.uow.users.get_by_email(email)
        if existing_email:
            raise BusinessError("Email already registered", status_code=409)
        existing_phone = await self.uow.users.get_by_phone(phone)
        if existing_phone:
            raise BusinessError("Phone already registered", status_code=409)

        # Retrieve latest valid OTP from PostgreSQL
        otp_record = await self.uow.otps.get_latest_valid(email)
        if not otp_record:
            raise BusinessError("OTP expired or not found", status_code=400)
        if otp_record.otp != otp:
            raise BusinessError("Invalid OTP", status_code=400)

        # Mark OTP as used
        await self.uow.otps.mark_used(otp_record.id)
        await self.uow.commit()

        # Hash password and create user
        hashed_password = get_password_hash(password)
        user = await self.uow.users.create(
            email=email,
            phone=phone,
            full_name=full_name,
            password_hash=hashed_password,
            profile_image=profile_image,
            is_active=True,
            is_verified=True,
        )
        await self.uow.commit()
        return user

    # ============================================================
    # OLD Registration Flow (Deprecated – kept for backward compatibility)
    # ============================================================

    async def request_otp(self, identifier: str) -> dict:
        """
        DEPRECATED: Use request_registration_otp instead.
        """
        # Check if identifier already registered
        existing_email = await self.uow.users.get_by_email(identifier)
        if existing_email:
            raise BusinessError("Email already registered", status_code=409)
        existing_phone = await self.uow.users.get_by_phone(identifier)
        if existing_phone:
            raise BusinessError("Phone already registered", status_code=409)

        otp = self._generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.otp_expiry_seconds)
        otp_record = await self.uow.otps.create_otp(identifier, otp, expires_at)
        await self.uow.commit()

        if "@" in identifier:
            try:
                success = await email_service.send_otp_email(identifier, otp)
                if not success:
                    await self.uow.otps.mark_used(otp_record.id)
                    await self.uow.commit()
                    raise BusinessError(
                        "Failed to send OTP email. Please try again later.",
                        status_code=502
                    )
            except Exception as e:
                print(f"Failed to send email: {e}")
                raise BusinessError(
                    "Failed to send OTP email. Please try again later.",
                    status_code=502
                )
        else:
            print(f"SMS OTP for {identifier}: {otp}")

        return {
            "message": "OTP sent successfully",
            "identifier": identifier,
            "expires_in": self.otp_expiry_seconds,
        }

    async def resend_otp(self, identifier: str) -> dict:
        """
        DEPRECATED: Use request_registration_otp instead.
        """
        existing_email = await self.uow.users.get_by_email(identifier)
        if existing_email:
            raise BusinessError("Email already registered", status_code=409)
        existing_phone = await self.uow.users.get_by_phone(identifier)
        if existing_phone:
            raise BusinessError("Phone already registered", status_code=409)

        otp = self._generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.otp_expiry_seconds)
        otp_record = await self.uow.otps.create_otp(identifier, otp, expires_at)
        await self.uow.commit()

        if "@" in identifier:
            try:
                success = await email_service.send_otp_email(identifier, otp)
                if not success:
                    await self.uow.otps.mark_used(otp_record.id)
                    await self.uow.commit()
                    raise BusinessError(
                        "Failed to send OTP email. Please try again later.",
                        status_code=502
                    )
            except Exception as e:
                print(f"Failed to send email: {e}")
                raise BusinessError(
                    "Failed to send OTP email. Please try again later.",
                    status_code=502
                )
        else:
            print(f"SMS OTP for {identifier}: {otp}")

        return {
            "message": "OTP resent successfully",
            "identifier": identifier,
            "expires_in": self.otp_expiry_seconds,
        }

    async def verify_otp(self, identifier: str, otp: str) -> dict:
        """
        DEPRECATED: Use register_with_otp instead.
        """
        otp_record = await self.uow.otps.get_latest_valid(identifier)
        if not otp_record:
            raise BusinessError("OTP expired or not found", status_code=400)
        if otp_record.otp != otp:
            raise BusinessError("Invalid OTP", status_code=400)

        # Mark OTP as used
        await self.uow.otps.mark_used(otp_record.id)
        await self.uow.commit()

        return {
            "message": "OTP verified successfully",
            "identifier": identifier,
            "verified": True,
        }

    async def register_user(
        self,
        email: str,
        phone: str,
        full_name: str,
        password: str,
        profile_image: Optional[str] = None,
    ) -> User:
        """
        DEPRECATED: Use register_with_otp instead.
        """
        # Check duplicates
        existing_email = await self.uow.users.get_by_email(email)
        if existing_email:
            raise BusinessError("Email already registered", status_code=409)
        existing_phone = await self.uow.users.get_by_phone(phone)
        if existing_phone:
            raise BusinessError("Phone already registered", status_code=409)

        # Check if at least one identifier is verified (using DB)
        email_otp = await self.uow.otps.get_latest_valid(email)
        phone_otp = await self.uow.otps.get_latest_valid(phone)
        if not email_otp and not phone_otp:
            raise BusinessError(
                "OTP verification required. Please verify your email or phone.",
                status_code=400,
            )

        # Validate password
        password_error = self._validate_password_strength(password)
        if password_error:
            raise BusinessError(password_error, status_code=400)

        # Create user
        hashed_password = get_password_hash(password)
        user = await self.uow.users.create(
            email=email,
            phone=phone,
            full_name=full_name,
            password_hash=hashed_password,
            profile_image=profile_image,
            is_active=True,
            is_verified=True,
        )
        await self.uow.commit()

        # Mark OTP as used (for both email and phone if they exist)
        if email_otp:
            await self.uow.otps.mark_used(email_otp.id)
        if phone_otp:
            await self.uow.otps.mark_used(phone_otp.id)
        await self.uow.commit()

        return user

    # ============================================================
    # Authentication & Token Management
    # ============================================================

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