import pytest
from arielbot.domain.events import (
    DynamicDetected, LiveStatusChanged, BotConnected, BotDisconnected, BotShutdown,
)


class TestDynamicDetected:
    def test_create(self):
        e = DynamicDetected(
            dynamic=object(), dyn_id="123", uname="up",
            targets=[(1, 2)], rendered_image=b"\x00",
        )
        assert e.dyn_id == "123"
        assert len(e.targets) == 1


class TestLiveStatusChanged:
    def test_create_live_on(self):
        e = LiveStatusChanged(
            uid="1", uname="up", room_id="100", title="title",
            cover_url="http://x", is_live=True, targets=[(1, 2)],
        )
        assert e.is_live is True

    def test_create_live_off(self):
        e = LiveStatusChanged(
            uid="1", uname="up", room_id="100", title="title",
            cover_url="http://x", is_live=False, targets=[],
        )
        assert e.is_live is False


class TestBotConnected:
    def test_create(self):
        e = BotConnected(bot_id=123)
        assert e.bot_id == 123


class TestBotDisconnected:
    def test_create(self):
        e = BotDisconnected(bot_id=456)
        assert e.bot_id == 456


class TestBotShutdown:
    def test_create(self):
        e = BotShutdown()
        assert isinstance(e, BotShutdown)
