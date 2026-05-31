import pytest
import pickle
from unittest.mock import AsyncMock, MagicMock
from arielbot.application.query_service import QueryService


class FakeHeader:
    def __init__(self, mid="", name=""):
        self.mid = mid
        self.name = name


class FakeDynamic:
    def __init__(self, message_id="", header=None, major=None):
        self.message_id = message_id
        self.header = header
        self.major = major

    def __reduce__(self):
        return (FakeDynamic, (self.message_id, self.header, self.major))


class FakePic:
    def __init__(self, url=""):
        self.url = url


class FakeOpus:
    def __init__(self, pics=None):
        self.pics = pics or []


class FakeMajor:
    def __init__(self, type="", opus=None):
        self.type = type
        self.opus = opus


@pytest.fixture
def mock_api():
    return AsyncMock()


@pytest.fixture
def mock_dyn_cache():
    return AsyncMock()


@pytest.fixture
def mock_channel_repo():
    return AsyncMock()


@pytest.fixture
def mock_dyn_renderer():
    return AsyncMock()


@pytest.fixture
def mock_sub_list_renderer():
    return AsyncMock()


@pytest.fixture
def service(mock_api, mock_dyn_cache, mock_channel_repo, mock_dyn_renderer, mock_sub_list_renderer):
    return QueryService(mock_api, mock_dyn_cache, mock_channel_repo, mock_dyn_renderer, mock_sub_list_renderer)


class TestGetDynImage:
    async def test_cache_hit(self, service, mock_dyn_cache, mock_dyn_renderer):
        dyn = FakeDynamic(message_id="123", header=FakeHeader(name="up"))
        mock_dyn_cache.exists.return_value = pickle.dumps(dyn)
        mock_dyn_renderer.render.return_value = b"img"
        result = await service.get_dyn_image("123")
        assert result == b"img"
        service._api.get_dynamic_by_id.assert_not_called()

    async def test_cache_miss_fetch_and_render(self, service, mock_api, mock_dyn_cache, mock_dyn_renderer):
        mock_dyn_cache.exists.return_value = None
        dyn = FakeDynamic(message_id="123", header=FakeHeader(name="up"))
        mock_api.get_dynamic_by_id.return_value = dyn
        mock_dyn_renderer.render.return_value = b"img"
        result = await service.get_dyn_image("123")
        assert result == b"img"
        mock_dyn_cache.save.assert_called_once()

    async def test_cache_miss_api_returns_none(self, service, mock_api, mock_dyn_cache):
        mock_dyn_cache.exists.return_value = None
        mock_api.get_dynamic_by_id.return_value = None
        result = await service.get_dyn_image("123")
        assert result is None


class TestGetDynImages:
    async def test_cache_hit_opus_type(self, service, mock_dyn_cache):
        dyn = FakeDynamic(
            message_id="123",
            header=FakeHeader(name="up"),
            major=FakeMajor(type="MAJOR_TYPE_OPUS", opus=FakeOpus(pics=[FakePic(url="http://img.url")])),
        )
        mock_dyn_cache.exists.return_value = pickle.dumps(dyn)
        result = await service.get_dyn_images("123")
        assert "http://img.url" in str(result)

    async def test_cache_hit_no_images(self, service, mock_dyn_cache):
        dyn = FakeDynamic(message_id="123", header=FakeHeader(name="up"), major=FakeMajor(type="OTHER"))
        mock_dyn_cache.exists.return_value = pickle.dumps(dyn)
        result = await service.get_dyn_images("123")
        assert result == "此动态没有图片"

    async def test_cache_miss_api_none(self, service, mock_api, mock_dyn_cache):
        mock_dyn_cache.exists.return_value = None
        mock_api.get_dynamic_by_id.return_value = None
        result = await service.get_dyn_images("123")
        assert result is None


class TestGetSubList:
    async def test_empty_list(self, service, mock_channel_repo):
        mock_channel_repo.list_by_group.return_value = []
        result = await service.get_sub_list(1, 2)
        assert result is None

    async def test_has_data(self, service, mock_channel_repo, mock_sub_list_renderer):
        mock_channel_repo.list_by_group.return_value = [("1", "name", 1, 1)]
        mock_sub_list_renderer.render.return_value = b"img"
        result = await service.get_sub_list(1, 2)
        assert result == b"img"


class TestGetHelpImage:
    async def test_returns_url(self, service):
        result = await service.get_help_image()
        assert "hdslb.com" in result