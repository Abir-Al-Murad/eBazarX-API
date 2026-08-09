from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Sequence, TypeVar, Generic
from uuid import UUID

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get(self, id: UUID) -> Optional[T]:
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[T]:
        pass
    
    @abstractmethod
    async def create(self, **kwargs) -> T:
        pass
    
    @abstractmethod
    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        pass

# We'll define specific interfaces later; they can be empty subclasses.