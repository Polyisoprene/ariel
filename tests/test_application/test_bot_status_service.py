import pytest
from unittest.mock import AsyncMock
from arielbot.application.bot_status_service import BotStatusService
from arielbot.domain.entities import BotStatus


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_event_bus():
    return AsyncMock()


@pytest.fixture
def service(mock_repo, mock_event_bus):
    return BotStatusService(mock_repo, mock_event_bus)


def _status(push_active, bot_active):
    return BotStatus(bot_id=1, group_id=2, push_active=push_active, bot_active=bot_active)


class TestTogglePush:
    async def test_new_bot_active(self, service, mock_repo):
        mock_repo.get.return_value = None
        result = await service.toggle_push(1, 2, True)
        assert result == "bot已开启"
        mock_repo.save.assert_called_once_with(1, 2, 1, 1)

    async def test_new_bot_inactive(self, service, mock_repo):
        mock_repo.get.return_value = None
        result = await service.toggle_push(1, 2, False)
        assert result == "bot已关闭"
        mock_repo.save.assert_called_once_with(1, 2, 0, 1)

    async def test_already_on(self, service, mock_repo):
        mock_repo.get.return_value = _status(True, True)
        result = await service.toggle_push(1, 2, True)
        assert result == "bot已经为开启状态"

    async def test_already_off(self, service, mock_repo):
        mock_repo.get.return_value = _status(False, True)
        result = await service.toggle_push(1, 2, False)
        assert result == "bot已经为关闭状态"

    async def test_turn_off(self, service, mock_repo):
        mock_repo.get.return_value = _status(True, True)
        result = await service.toggle_push(1, 2, False)
        assert result == "bot关闭成功"
        mock_repo.update_push.assert_called_once_with(1, 2, 0)

    async def test_turn_on(self, service, mock_repo):
        mock_repo.get.return_value = _status(False, True)
        result = await service.toggle_push(1, 2, True)
        assert result == "bot开启成功"
        mock_repo.update_push.assert_called_once_with(1, 2, 1)


class TestIsBotActive:
    async def test_no_record_creates(self, service, mock_repo):
        mock_repo.get.return_value = None
        result = await service.is_bot_active(1, 2)
        assert result is True
        mock_repo.save.assert_called_once_with(1, 2, 1, 1)

    async def test_active(self, service, mock_repo):
        mock_repo.get.return_value = _status(True, True)
        result = await service.is_bot_active(1, 2)
        assert result is True

    async def test_inactive_push(self, service, mock_repo):
        mock_repo.get.return_value = _status(False, True)
        result = await service.is_bot_active(1, 2)
        assert result is False

    async def test_inactive_bot(self, service, mock_repo):
        mock_repo.get.return_value = _status(True, False)
        result = await service.is_bot_active(1, 2)
        assert result is False


class TestLifecycle:
    async def test_on_connect(self, service, mock_repo):
        await service.on_bot_connect(1)
        mock_repo.update_active.assert_called_once_with(1, 1)

    async def test_on_disconnect(self, service, mock_repo):
        await service.on_bot_disconnect(1)
        mock_repo.update_active.assert_called_once_with(1, 0)

    async def test_shutdown_all(self, service, mock_repo):
        mock_repo.list_all_bots.return_value = [1, 2, 3]
        await service.shutdown_all()
        assert mock_repo.update_active.call_count == 3
        mock_repo.update_active.assert_any_call(1, 0)
        mock_repo.update_active.assert_any_call(2, 0)
        mock_repo.update_active.assert_any_call(3, 0)

    async def test_shutdown_no_bots(self, service, mock_repo):
        mock_repo.list_all_bots.return_value = []
        await service.shutdown_all()
        mock_repo.update_active.assert_not_called()