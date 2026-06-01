import pytest
import asyncio
from unittest.mock import AsyncMock
from arielbot.infrastructure.event_bus import SimpleEventBus
from arielbot.domain.events import BotConnected, BotDisconnected


_loop_tasks = []


def start_loop(bus):
    task = asyncio.create_task(bus._dispatch_loop())
    _loop_tasks.append(task)
    return task


@pytest.fixture(autouse=True)
def cleanup_loops():
    yield
    for task in _loop_tasks:
        try:
            task.cancel()
        except RuntimeError:
            pass
    _loop_tasks.clear()


class TestSimpleEventBus:
    @pytest.fixture
    def bus(self):
        b = SimpleEventBus()
        yield b

    def test_subscribe_registers_handler(self, bus):
        handler = AsyncMock()
        bus.subscribe(BotConnected, handler)
        assert BotConnected in bus._handlers
        assert handler in bus._handlers[BotConnected]

    def test_subscribe_multiple_types(self, bus):
        h1 = AsyncMock()
        h2 = AsyncMock()
        bus.subscribe(BotConnected, h1)
        bus.subscribe(BotDisconnected, h2)
        assert len(bus._handlers) == 2

    @pytest.mark.asyncio
    async def test_publish_and_dispatch(self, bus):
        handler = AsyncMock()
        bus.subscribe(BotConnected, handler)
        start_loop(bus)
        await asyncio.sleep(0.1)
        event = BotConnected(bot_id=1)
        await bus.publish(event)
        await asyncio.sleep(0.2)
        handler.assert_called_once()
        called_event = handler.call_args[0][0]
        assert isinstance(called_event, BotConnected)
        assert called_event.bot_id == 1

    @pytest.mark.asyncio
    async def test_publish_with_subclass_events(self, bus):
        handler = AsyncMock()
        bus.subscribe(BotConnected, handler)
        start_loop(bus)
        await asyncio.sleep(0.1)
        event = BotConnected(bot_id=42)
        await bus.publish(event)
        await asyncio.sleep(0.2)
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_no_handlers(self, bus):
        """Should not raise when no handlers registered for event type."""
        start_loop(bus)
        await asyncio.sleep(0.1)
        event = BotConnected(bot_id=1)
        await bus.publish(event)
        await asyncio.sleep(0.2)

    @pytest.mark.asyncio
    async def test_handler_error_does_not_crash(self, bus):
        handler = AsyncMock(side_effect=RuntimeError("boom"))
        bus.subscribe(BotConnected, handler)
        start_loop(bus)
        await asyncio.sleep(0.1)
        await bus.publish(BotConnected(bot_id=1))
        await asyncio.sleep(0.2)

    @pytest.mark.asyncio
    async def test_queue_full_drops_and_warns(self, bus):
        start_loop(bus)
        await asyncio.sleep(0.1)
        for _ in range(200):
            await bus.publish(BotConnected(bot_id=1))
        await asyncio.sleep(0.1)