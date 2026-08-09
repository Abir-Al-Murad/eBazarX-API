from abc import ABC, abstractmethod
from app.domain.events import DomainEvent

class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        pass