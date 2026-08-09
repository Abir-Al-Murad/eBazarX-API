import re
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


class AuthService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ---------- Password strength validation ----------
    def _validate_password_strength(self, password: str) -> Optional[List[str]]:
        """
        Returns a list of error messages if the password is weak,
        otherwise returns None.
        """
        errors = []

        # Minimum length
        min_len = getattr(settings, "PASSWORD_MIN_LENGTH", 8)
        if len(password) < min_len:
            errors.append(f"Password must be at least {min_len} characters long.")

        # Uppercase
        if getattr(settings, "PASSWORD_REQUIRE_UPPERCASE", True) and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter.")

        # Lowercase
        if getattr(settings, "PASSWORD_REQUIRE_LOWERCASE", True) and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter.")

        # Digit
        if getattr(settings, "PASSWORD_REQUIRE_DIGIT", True) and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit.")

        # Special character
        if getattr(settings, "PASSWORD_REQUIRE_SPECIAL", True) and not re.search(
            r"[!@#$%^&*(),.?\":{}|<>]", password
        ):
            errors.append("Password must contain at least one special character (e.g., !@#$%^&*).")

        # Optional: disallow common passwords (you could extend with a list)
        if getattr(settings, "PASSWORD_DISALLOW_COMMON", False):
            common_passwords = {"password", "12345678", "qwerty", "password123"}  # load from settings maybe
            if password.lower() in common_passwords:
                errors.append("Password is too common. Please choose a more secure password.")

        return errors if errors else None

    # ---------- Registration (with password validation) ----------
    async def register_user(
        self,
        email: str,
        phone: str,
        full_name: str,
        password: str,
    ):
        # 1. Check existing email
        existing = await self.uow.users.get_by_email(email)
        if existing:
            raise BusinessError("Email already registered", status_code=409)

        # 2. Check existing phone
        existing_phone = await self.uow.users.get_by_phone(phone)
        if existing_phone:
            raise BusinessError("Phone already registered", status_code=409)

        # 3. Validate password strength
        password_errors = self._validate_password_strength(password)
        if password_errors:
            # Combine errors into a single readable message
            error_msg = "; ".join(password_errors)
            raise BusinessError(f"Password validation failed: {error_msg}", status_code=400)

        # 4. Create user
        user = await self.uow.users.create(
            email=email,
            phone=phone,
            full_name=full_name,
            password_hash=get_password_hash(password),
            is_active=True,
            is_verified=False,
        )

        await self.uow.commit()
        return user

    # ---------- Authentication (unchanged) ----------
    async def authenticate(
        self,
        login: str,
        password: str,
    ):
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

        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role.value}
        )
        refresh_token = create_refresh_token(
            {"sub": str(user.id)}
        )

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
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

    # ---------- Refresh (unchanged) ----------
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

        new_access = create_access_token(
            {"sub": str(user_id), "role": payload.get("role")}
        )
        new_refresh = create_refresh_token(
            {"sub": str(user_id), "role": payload.get("role")}
        )

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
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