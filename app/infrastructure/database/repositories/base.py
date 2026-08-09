from typing import TypeVar, Generic, Type, Optional, List, Dict, Any,Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.domain.interfaces.repositories import BaseRepository as DomainBaseRepo

ModelType = TypeVar("ModelType")

class AsyncBaseRepository(DomainBaseRepo[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> Optional[ModelType]:
        result = await self.session.execute(select(self.model).filter(self.model.id == id))  # type: ignore
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        result = await self.session.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        return instance

    async def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        stmt = update(self.model).where(self.model.id == id).values(**kwargs).returning(self.model) # type: ignore
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, id: UUID) -> bool:
        stmt = delete(self.model).where(self.model.id == id) # type: ignore
        result = await self.session.execute(stmt)
        return result.rowcount > 0