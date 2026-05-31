import pytest
import asyncio
import pickle
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from arielbot.application.auth_service import AuthService


class FakeResponse:
    pass


class MockDynamic:
    def __init__(self, message_id, mid, name):
        self.message_id = message_id
        self.header = MagicMock()
        self.header.mid = mid
        self.header.name = name
        self.__reduce_ex__ = None


class MockOpusDynamic:
    def __init__(self, message_id):
        self.message_id = message_id
        self.header = MagicMock()
        self.header.mid = "123"
        self.header.name = "up"
        self.major = MagicMock()
        self.major.type = "MAJOR_TYPE_OPUS"
        self.major.opus = MagicMock()
        self.major.opus.pics = []
        self.__reduce_ex__ = None


@pytest.fixture
def mock_auth_api():
    return AsyncMock()


@pytest.fixture
def mock_cookie_repo():
    return AsyncMock()


@pytest.fixture
def mock_bot_client():
    return AsyncMock()


@pytest.fixture
def mock_bot():
    return AsyncMock()


@pytest.fixture
def mock_event():
    return MagicMock()


@pytest.fixture
def mock_cookie_manager():
    return AsyncMock()


@pytest.fixture
def service(mock_auth_api, mock_cookie_repo, mock_bot_client, mock_cookie_manager):
    def identity(x):
        return x
    return AuthService(
        mock_auth_api, mock_cookie_repo, mock_bot_client,
        identity, identity,
        cookie_manager=mock_cookie_manager,
    )


class TestLogin:
    async def test_get_qrcode_fails(self, service, mock_auth_api, mock_bot, mock_event):
        mock_auth_api.get_qrcode.return_value = None
        await service.login(mock_bot, mock_event)
        mock_bot.send.assert_called()

    async def test_poll_returns_none(self, service, mock_auth_api, mock_bot, mock_event):
        mock_auth_api.get_qrcode.return_value = "http://qr"
        mock_auth_api.poll_scan.return_value = None
        await service.login(mock_bot, mock_event)
        mock_bot.send.assert_any_call(mock_event, "登陆失败")

    async def test_poll_code_86038(self, service, mock_auth_api, mock_bot, mock_event):
        mock_auth_api.get_qrcode.return_value = "http://qr"
        mock_auth_api.poll_scan.return_value = {"code": 86038}
        await service.login(mock_bot, mock_event)
        mock_bot.send.assert_any_call(mock_event, "登陆失败")

    async def test_login_success(self, service, mock_auth_api, mock_cookie_repo, mock_bot, mock_event, mock_cookie_manager):
        mock_auth_api.get_qrcode.return_value = "http://qr"
        mock_auth_api.poll_scan.return_value = {
            "code": 0, "url": "http://x?DedeUserID=1",
            "refresh_token": "token",
        }
        await service.login(mock_bot, mock_event)
        mock_cookie_repo.clear.assert_called_once()
        mock_cookie_repo.save.assert_called_once()
        mock_cookie_manager.load_cookie.assert_called_once()

    async def test_cookie_parse_fails(self, service, mock_auth_api, mock_bot, mock_event):
        service._parse_cookie = lambda x: None
        mock_auth_api.get_qrcode.return_value = "http://qr"
        mock_auth_api.poll_scan.return_value = {
            "code": 0, "url": "http://x", "refresh_token": "t",
        }
        await service.login(mock_bot, mock_event)
        mock_bot.send.assert_any_call(mock_event, ANY)

    async def test_no_refresh_token(self, service, mock_auth_api, mock_bot, mock_event):
        mock_auth_api.get_qrcode.return_value = "http://qr"
        mock_auth_api.poll_scan.return_value = {"code": 0, "url": "http://x"}
        await service.login(mock_bot, mock_event)
        mock_bot.send.assert_any_call(mock_event, ANY)

    async def test_timeout(self, service, mock_auth_api, mock_bot, mock_event):
        mock_auth_api.get_qrcode.return_value = "http://qr"
        mock_auth_api.poll_scan.return_value = {"code": 1}

        async def fake_poll():
            await asyncio.sleep(999)

        mock_auth_api.poll_scan.side_effect = fake_poll

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(service._poll_scan_result(), timeout=0.01)