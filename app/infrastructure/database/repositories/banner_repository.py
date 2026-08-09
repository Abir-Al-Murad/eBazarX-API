from sqlalchemy import or_, select, and_
from datetime import datetime
from uuid import UUID
from typing import Optional, Sequence
from app.infrastructure.database.models import Banner
from .base import AsyncBaseRepository

class BannerRepository(AsyncBaseRepository[Banner]):
    async def get(self, id: UUID) -> Optional[Banner]:
        result = await self.session.execute(
            select(Banner).filter(Banner.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Banner]:
        result = await self.session.execute(
            select(Banner).offset(skip).limit(limit).order_by(Banner.position)
        )
        return result.scalars().all()



    async def get_active_banners(self, current_time: datetime):
        result = await self.session.execute(
         select(Banner)
         .where(
                Banner.is_active.is_(True),
             or_(
                 Banner.start_date.is_(None),
                 Banner.start_date <= current_time,
             ),
             or_(
                 Banner.end_date.is_(None),
                 Banner.end_date >= current_time,
             ),
        )
         .order_by(Banner.position)
    )

        return result.scalars().all()