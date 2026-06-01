import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from arielbot.infrastructure.adapters.bili_cookie_utils import (
    parse_login_cookie, serialize_cookie, deserialize_cookie,
)
from arielbot.infrastructure.adapters.bot_client import BotClient


class TestBiliWbi:
    def test_parse_login_cookie(self):
        result = {
            "url": "http://x?DedeUserID=1&SESSDATA=sess&bili_jct=jct&gourl=http://g",
        }
        cookies = parse_login_cookie(result)
        assert cookies is not None
        assert cookies["DedeUserID"] == "1"
        assert cookies["SESSDATA"] == "sess"
        assert "gourl" not in cookies

    def test_parse_login_cookie_no_url(self):
        assert parse_login_cookie({"url": ""}) is None

    def test_serialize_roundtrip(self):
        data = {"a": "b", "c": 1}
        blob = serialize_cookie(data)
        restored = deserialize_cookie(blob)
        assert restored == data


class TestBotClient:
    @pytest.mark.asyncio
    @patch("arielbot.infrastructure.adapters.bot_client.get_bot")
    async def test_send_group_msg_bot_not_found(self, mock_get_bot):
        mock_get_bot.side_effect = KeyError("not found")
        client = BotClient()
        await client.send_group_msg(100, 999)

    @pytest.mark.asyncio
    @patch("arielbot.infrastructure.adapters.bot_client.get_bot")
    async def test_send_group_msg(self, mock_get_bot):
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot
        client = BotClient()
        await client.send_group_msg(100, 1, text="hello", image=b"img")
        mock_bot.send_group_msg.assert_called_once()