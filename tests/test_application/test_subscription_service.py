import pytest
import pickle
from unittest.mock import AsyncMock, MagicMock
from arielbot.application.subscription_service import SubscriptionService
from arielbot.domain.entities import SubTarget, SubChannel


@pytest.fixture
def mock_api():
    return AsyncMock()


@pytest.fixture
def mock_target_repo():
    return AsyncMock()


@pytest.fixture
def mock_channel_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_api, mock_target_repo, mock_channel_repo):
    return SubscriptionService(mock_api, mock_target_repo, mock_channel_repo)


def _target(nickname="name", uid="123"):
    return SubTarget(uid=uid, nickname=nickname, live_status=0)


def _ch(live_active=True, dyn_active=True, uid="123", gid=100, bid=200):
    return SubChannel(uid=uid, group_id=gid, bot_id=bid, live_active=live_active, dyn_active=dyn_active)


class TestAddSub:
    async def test_already_subscribed_in_group(self, service, mock_target_repo, mock_channel_repo):
        mock_target_repo.get.return_value = _target()
        mock_channel_repo.get.return_value = _ch(True, True)
        result = await service.add_sub("123", 100, 200)
        assert "本群已订阅过" in result

    async def test_re_enable_disabled_sub(self, service, mock_target_repo, mock_channel_repo):
        mock_target_repo.get.return_value = _target()
        mock_channel_repo.get.return_value = _ch(False, False)
        result = await service.add_sub("123", 100, 200)
        assert "成功添加订阅" in result
        mock_channel_repo.update.assert_called_once_with(1, 1, "123", 100, 200)

    async def test_subscribed_target_new_group(self, service, mock_target_repo, mock_channel_repo):
        mock_target_repo.get.return_value = _target()
        mock_channel_repo.get.return_value = None
        result = await service.add_sub("123", 100, 200)
        assert "成功添加订阅" in result
        mock_channel_repo.save.assert_called_once_with("123", 100, 200)

    async def test_new_sub_already_following(self, service, mock_api, mock_target_repo, mock_channel_repo):
        mock_target_repo.get.return_value = None
        mock_api.get_user_info.return_value = {
            "following": True,
            "card": {"name": "upname"},
        }
        result = await service.add_sub("123", 100, 200)
        assert "成功添加订阅 --> upname(123)" == result
        mock_api.follow_user.assert_not_called()
        mock_target_repo.save.assert_called_once_with("123", "upname", 0)

    async def test_new_sub_not_following_auto_follow(self, service, mock_api, mock_target_repo, mock_channel_repo):
        mock_target_repo.get.return_value = None
        mock_api.get_user_info.return_value = {
            "following": False,
            "card": {"name": "upname"},
        }
        mock_api.follow_user.return_value = True
        result = await service.add_sub("123", 100, 200)
        assert "成功添加订阅" in result
        mock_api.follow_user.assert_called_once_with("123", 1)

    async def test_new_sub_follow_fails(self, service, mock_api, mock_target_repo):
        mock_target_repo.get.return_value = None
        mock_api.get_user_info.return_value = {
            "following": False,
            "card": {"name": "upname"},
        }
        mock_api.follow_user.return_value = None
        result = await service.add_sub("123", 100, 200)
        assert result == "添加订阅失败"

    async def test_user_not_found(self, service, mock_api, mock_target_repo):
        mock_target_repo.get.return_value = None
        mock_api.get_user_info.return_value = "未找到相关UP信息"
        result = await service.add_sub("123", 100, 200)
        assert result == "未找到相关UP信息"

    async def test_missing_card_key(self, service, mock_api, mock_target_repo):
        mock_target_repo.get.return_value = None
        mock_api.get_user_info.return_value = {"following": True}
        result = await service.add_sub("123", 100, 200)
        assert result == "未找到相关UP信息"


class TestDelSub:
    async def test_not_subscribed(self, service, mock_channel_repo):
        mock_channel_repo.get.return_value = None
        result = await service.del_sub("123", 100, 200)
        assert "本群没有订阅" in result

    async def test_delete_success(self, service, mock_target_repo, mock_channel_repo):
        mock_channel_repo.get.return_value = _ch()
        mock_target_repo.get.return_value = _target()
        result = await service.del_sub("123", 100, 200)
        assert "成功删除订阅 --> name(123)" == result
        mock_channel_repo.update.assert_called_once_with(0, 0, "123", 100, 200)

    async def test_delete_target_missing(self, service, mock_target_repo, mock_channel_repo):
        mock_channel_repo.get.return_value = _ch()
        mock_target_repo.get.return_value = None
        result = await service.del_sub("123", 100, 200)
        assert "成功删除订阅 --> 123" == result


class TestToggleLive:
    async def test_not_subscribed(self, service, mock_channel_repo):
        mock_channel_repo.get.return_value = None
        result = await service.toggle_live("123", 100, 200, True)
        assert "本群没有订阅" in result

    async def test_enable(self, service, mock_channel_repo):
        mock_channel_repo.get.return_value = _ch(False, True)
        result = await service.toggle_live("123", 100, 200, True)
        assert result == "开启直播推送成功"
        mock_channel_repo.update.assert_called_once_with(1, 1, "123", 100, 200)

    async def test_disable(self, service, mock_channel_repo):
        mock_channel_repo.get.return_value = _ch(True, True)
        result = await service.toggle_live("123", 100, 200, False)
        assert result == "关闭直播推送成功"
        mock_channel_repo.update.assert_called_once_with(0, 1, "123", 100, 200)


class TestToggleDyn:
    async def test_not_subscribed(self, service, mock_channel_repo):
        mock_channel_repo.get.return_value = None
        result = await service.toggle_dyn("123", 100, 200, True)
        assert "本群没有订阅" in result

    async def test_enable(self, service, mock_channel_repo):
        mock_channel_repo.get.return_value = _ch(True, False)
        result = await service.toggle_dyn("123", 100, 200, True)
        assert result == "开启动态推送成功"
        mock_channel_repo.update.assert_called_once_with(1, 1, "123", 100, 200)

    async def test_disable(self, service, mock_channel_repo):
        mock_channel_repo.get.return_value = _ch(True, True)
        result = await service.toggle_dyn("123", 100, 200, False)
        assert result == "关闭动态推送成功"
        mock_channel_repo.update.assert_called_once_with(1, 0, "123", 100, 200)
