from sqlalchemy import select, and_, update
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from app.infrastructure.database.models import OTP
from .base import AsyncBaseRepository

class OTPRepository(AsyncBaseRepository[OTP]):
    async def create_otp(self, email: str, otp: str, expires_at: datetime) -> OTP:
        """Create a new OTP record."""
        return await self.create(
            email=email,
            otp=otp,
            expires_at=expires_at,
            used=False,
        )

    async def get_latest_valid(self, email: str) -> Optional[OTP]:
        """Get the latest valid (not used, not expired) OTP for email."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(OTP)
            .where(
                and_(
                    OTP.email == email,
                    OTP.used == False,
                    OTP.expires_at > now,
                )
            )
            .order_by(OTP.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(self, otp_id: UUID) -> None:
        """Mark an OTP as used (without committing)."""
        stmt = update(OTP).where(OTP.id == otp_id).values(used=True)
        await self.session.execute(stmt)

    async def delete_expired(self) -> int:
        """Delete all expired OTPs (without committing)."""
        now = datetime.now(timezone.utc)
        stmt = select(OTP).where(OTP.expires_at <= now)
        result = await self.session.execute(stmt)
        expired = result.scalars().all()
        for otp in expired:
            await self.delete(otp.id)
        return len(expired)