import pytest
from unittest.mock import AsyncMock, MagicMock
from arielbot.presentation.middleware import make_bot_is_active_rule
from nonebot.adapters.onebot.v11 import GroupMessageEvent


class TestMiddleware:
    @pytest.mark.asyncio
    async def test_bot_is_active_creates_and_returns_true(self):
        svc = AsyncMock()
        svc.is_bot_active.return_value = True
        event = MagicMock(spec=GroupMessageEvent)
        event.self_id = 1
        event.group_id = 2
        rule = make_bot_is_active_rule(svc)
        result = await rule(event)
        assert result is True
        svc.is_bot_active.assert_called_once_with(1, 2)

    @pytest.mark.asyncio
    async def test_bot_is_active_returns_false(self):
        svc = AsyncMock()
        svc.is_bot_active.return_value = False
        event = MagicMock(spec=GroupMessageEvent)
        event.self_id = 1
        event.group_id = 2
        rule = make_bot_is_active_rule(svc)
        result = await rule(event)
        assert result is False