from sqlalchemy import select, delete
from uuid import UUID
from typing import Optional, Sequence
from datetime import datetime, timezone
from app.infrastructure.database.models import RefreshToken
from .base import AsyncBaseRepository

class RefreshTokenRepository(AsyncBaseRepository[RefreshToken]):
    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        result = await self.session.execute(
            select(RefreshToken).filter(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def get_valid_by_user(self, user_id: UUID) -> Sequence[RefreshToken]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.expires_at > now,
                RefreshToken.revoked == False
            )
        )
        return result.scalars().all()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self.session.execute(
            delete(RefreshToken).where(RefreshToken.user_id == user_id)
        )