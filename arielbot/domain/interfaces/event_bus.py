from abc import ABC, abstractmethod
from typing import Any, Callable, Type


class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: Any) -> None:
        ...

    @abstractmethod
    def subscribe(self, event_type: Type, handler: Callable) -> None:
        ...