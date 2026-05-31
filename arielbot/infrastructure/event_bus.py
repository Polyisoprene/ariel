import asyncio
from typing import Any, Callable, Dict, List, Optional, Type
from nonebot import logger
from arielbot.domain.interfaces.event_bus import EventBus


class SimpleEventBus(EventBus):
    def __init__(self):
        self._handlers: Dict[Type, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._task: Optional[asyncio.Task] = None

    def subscribe(self, event_type: Type, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: Any) -> None:
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"EventBus queue full, dropping {type(event).__name__}")

    async def start(self) -> None:
        self._task = asyncio.create_task(self._dispatch_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _dispatch_loop(self):
        while True:
            event = await self._queue.get()
            for event_type, handlers in self._handlers.items():
                if isinstance(event, event_type):
                    for handler in handlers:
                        try:
                            await handler(event)
                        except Exception as e:
                            logger.error(
                                f"Event handler error for {type(event).__name__}: {e}"
                            )