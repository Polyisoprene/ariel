import pytest
from unittest.mock import AsyncMock, MagicMock
from arielbot.domain.events import (
    DynamicDetected, LiveStatusChanged, BotConnected, BotDisconnected, BotShutdown,
)
from arielbot.application.push.handlers import (
    DynPushHandler, LivePushHandler, BotLifecycleHandler,
)


@pytest.fixture
def mock_bot_client():
    return AsyncMock()


class TestDynPushHandler:
    async def test_handle_sends_to_all_targets(self, mock_bot_client):
        handler = DynPushHandler(mock_bot_client)
        event = DynamicDetected(
            dynamic=object(), dyn_id="123", uname="up",
            targets=[(100, 1), (200, 2)], rendered_image=b"img",
        )
        await handler.handle(event)
        assert mock_bot_client.send_group_msg.call_count == 2

    async def test_handle_message_format(self, mock_bot_client):
        handler = DynPushHandler(mock_bot_client)
        event = DynamicDetected(
            dynamic=object(), dyn_id="456", uname="the_up",
            targets=[(100, 1)], rendered_image=b"img",
        )
        await handler.handle(event)
        args, kwargs = mock_bot_client.send_group_msg.call_args
        assert args[2] == "the_up发布了新动态:\n\n传送门→https://t.bilibili.com/456"
        assert kwargs["image"] == b"img"


class TestLivePushHandler:
    async def test_handle_skips_when_not_live(self, mock_bot_client):
        handler = LivePushHandler(mock_bot_client)
        event = LiveStatusChanged(
            uid="1", uname="up", room_id="100", title="t",
            cover_url="http://c", is_live=False, targets=[(100, 1)],
        )
        await handler.handle(event)
        mock_bot_client.send_group_msg.assert_not_called()

    async def test_handle_sends_live_message(self, mock_bot_client):
        handler = LivePushHandler(mock_bot_client)
        event = LiveStatusChanged(
            uid="1", uname="up", room_id="100", title="hello world",
            cover_url="http://cover", is_live=True, targets=[(100, 1)],
        )
        await handler.handle(event)
        args, kwargs = mock_bot_client.send_group_msg.call_args
        assert "开播啦" in args[2]
        assert "hello world" in args[2]
        assert kwargs["cover"] == "http://cover"


class TestBotLifecycleHandler:
    async def test_on_connect(self):
        svc = AsyncMock()
        handler = BotLifecycleHandler(svc)
        await handler.on_connect(BotConnected(bot_id=42))
        svc.on_bot_connect.assert_called_once_with(42)

    async def test_on_disconnect(self):
        svc = AsyncMock()
        handler = BotLifecycleHandler(svc)
        await handler.on_disconnect(BotDisconnected(bot_id=99))
        svc.on_bot_disconnect.assert_called_once_with(99)

    async def test_on_shutdown(self):
        svc = AsyncMock()
        handler = BotLifecycleHandler(svc)
        await handler.on_shutdown(BotShutdown())
        svc.shutdown_all.assert_called_once()