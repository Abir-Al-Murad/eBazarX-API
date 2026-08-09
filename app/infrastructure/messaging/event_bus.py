from app.domain.interfaces.event_bus import EventBus
from app.domain.events import DomainEvent
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ebazar",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.infrastructure.messaging.tasks.event_handlers"]
)

class CeleryEventBus(EventBus):
    async def publish(self, event: DomainEvent) -> None:
        # Route to task based on event type
        task_name = f"handle_{event.__class__.__name__.lower()}"
        celery_app.send_task(task_name, args=[event], queue="events")