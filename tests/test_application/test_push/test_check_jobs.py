import pytest
import pickle
from unittest.mock import AsyncMock, MagicMock
from arielbot.application.push.check_jobs import DynCheckJob, LiveCheckJob
from arielbot.domain.events import DynamicDetected, LiveStatusChanged


class FakeHeader:
    def __init__(self, mid, name):
        self.mid = mid
        self.name = name

    def __reduce__(self):
        return (FakeHeader, (self.mid, self.name))


class FakeDynamic:
    def __init__(self, message_id, mid, name):
        self.message_id = message_id
        self.header = FakeHeader(mid, name)

    def __reduce__(self):
        return (FakeDynamic, (self.message_id, self.header.mid, self.header.name))


@pytest.fixture
def mock_api():
    return AsyncMock()


@pytest.fixture
def mock_dyn_cache():
    return AsyncMock()


@pytest.fixture
def mock_sub_channel():
    return AsyncMock()


@pytest.fixture
def mock_dyn_renderer():
    return AsyncMock()


@pytest.fixture
def mock_event_bus():
    return AsyncMock()


@pytest.fixture
def mock_target_repo():
    return AsyncMock()


@pytest.fixture
def dyn_job(mock_api, mock_dyn_cache, mock_sub_channel, mock_dyn_renderer, mock_event_bus):
    return DynCheckJob(mock_api, mock_dyn_cache, mock_sub_channel, mock_dyn_renderer, mock_event_bus)


@pytest.fixture
def live_job(mock_api, mock_target_repo, mock_sub_channel, mock_event_bus):
    return LiveCheckJob(mock_api, mock_target_repo, mock_sub_channel, mock_event_bus)


class TestDynCheckJob:
    async def test_api_returns_none(self, dyn_job, mock_api):
        mock_api.get_follow_dynamics.return_value = None
        await dyn_job.run()
        mock_api.get_follow_dynamics.assert_called_once()

    async def test_cached_dynamic_skipped(self, dyn_job, mock_api, mock_dyn_cache):
        dyn = FakeDynamic("123", "mid", "up")
        mock_api.get_follow_dynamics.return_value = [dyn]
        mock_dyn_cache.exists.return_value = b"cached"
        await dyn_job.run()
        mock_dyn_cache.save.assert_not_called()
        mock_dyn_renderer = dyn_job._dyn_renderer
        mock_dyn_renderer.render.assert_not_called()

    async def test_no_targets_still_caches(self, dyn_job, mock_api, mock_dyn_cache, mock_sub_channel):
        dyn = FakeDynamic("123", "mid", "up")
        mock_api.get_follow_dynamics.return_value = [dyn]
        mock_dyn_cache.exists.return_value = None
        mock_sub_channel.find_push_targets_for_dyn.return_value = []
        await dyn_job.run()
        mock_dyn_cache.save.assert_called_once()
        mock_dyn_renderer = dyn_job._dyn_renderer
        mock_dyn_renderer.render.assert_not_called()

    async def test_publishes_event(self, dyn_job, mock_api, mock_dyn_cache, mock_sub_channel, mock_dyn_renderer, mock_event_bus):
        dyn = FakeDynamic("456", "mid", "up2")
        mock_api.get_follow_dynamics.return_value = [dyn]
        mock_dyn_cache.exists.return_value = None
        mock_sub_channel.find_push_targets_for_dyn.return_value = [(100, 200)]
        mock_dyn_renderer.render.return_value = b"rendered"
        await dyn_job.run()
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, DynamicDetected)
        assert event.dyn_id == "456"
        assert event.rendered_image == b"rendered"

    async def test_multiple_dynamics(self, dyn_job, mock_api, mock_dyn_cache, mock_sub_channel, mock_dyn_renderer, mock_event_bus):
        d1 = FakeDynamic("1", "m1", "u1")
        d2 = FakeDynamic("2", "m2", "u2")
        mock_api.get_follow_dynamics.return_value = [d1, d2]
        mock_dyn_cache.exists.return_value = None
        mock_sub_channel.find_push_targets_for_dyn.return_value = [(1, 2)]
        mock_dyn_renderer.render.return_value = b"img"
        await dyn_job.run()
        assert mock_event_bus.publish.call_count == 2


class TestLiveCheckJob:
    async def test_no_uids(self, live_job, mock_sub_channel):
        mock_sub_channel.find_live_check_uids.return_value = []
        await live_job.run()

    async def test_api_returns_none(self, live_job, mock_sub_channel, mock_api):
        mock_sub_channel.find_live_check_uids.return_value = [("1", 0)]
        mock_api.get_room_info_by_uids.return_value = None
        await live_job.run()
        mock_api.get_room_info_by_uids.assert_called_once()

    async def test_status_unchanged(self, live_job, mock_sub_channel, mock_api, mock_target_repo):
        mock_sub_channel.find_live_check_uids.return_value = [("1", 0)]
        mock_api.get_room_info_by_uids.return_value = {
            "1": {"live_status": 0, "uid": "1", "uname": "up", "room_id": "100"},
        }
        await live_job.run()
        mock_target_repo.update.assert_not_called()
        mock_event_bus = live_job._event_bus
        mock_event_bus.publish.assert_not_called()

    async def test_live_started_publishes_event(self, live_job, mock_sub_channel, mock_api, mock_target_repo):
        mock_sub_channel.find_live_check_uids.return_value = [("1", 0)]
        mock_api.get_room_info_by_uids.return_value = {
            "1": {"live_status": 1, "uid": "1", "uname": "up",
                  "room_id": "100", "title": "t", "cover_from_user": "http://c"},
        }
        mock_sub_channel.find_push_targets_for_live.return_value = [(100, 200)]
        mock_event_bus = live_job._event_bus
        await live_job.run()
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, LiveStatusChanged)
        assert event.is_live is True

    async def test_live_ended_updates_target(self, live_job, mock_sub_channel, mock_api, mock_target_repo):
        mock_sub_channel.find_live_check_uids.return_value = [("1", 1)]
        mock_api.get_room_info_by_uids.return_value = {
            "1": {"live_status": 0, "uid": "1", "uname": "up"},
        }
        await live_job.run()
        mock_target_repo.update.assert_called_once_with("up", 0, "1")

    async def test_live_started_no_targets(self, live_job, mock_sub_channel, mock_api, mock_target_repo):
        mock_sub_channel.find_live_check_uids.return_value = [("1", 0)]
        mock_api.get_room_info_by_uids.return_value = {
            "1": {"live_status": 1, "uid": "1", "uname": "up",
                  "room_id": "100", "title": "t", "cover_from_user": "http://c"},
        }
        mock_sub_channel.find_push_targets_for_live.return_value = []
        mock_event_bus = live_job._event_bus
        await live_job.run()
        mock_event_bus.publish.assert_not_called()