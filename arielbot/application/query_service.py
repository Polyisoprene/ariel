import pickle
from typing import List, Optional
from arielbot.domain.interfaces.api import BiliContentAPI
from arielbot.domain.interfaces.repository import DynCacheRepository, SubChannelRepository
from arielbot.domain.interfaces.renderer import DynRenderer, SubListRenderer


class QueryService:
    def __init__(self, content_api: BiliContentAPI,
                 dyn_cache_repo: DynCacheRepository,
                 sub_channel_repo: SubChannelRepository,
                 dyn_renderer: DynRenderer,
                 sub_list_renderer: SubListRenderer):
        self._api = content_api
        self._dyn_cache_repo = dyn_cache_repo
        self._sub_channel_repo = sub_channel_repo
        self._dyn_renderer = dyn_renderer
        self._sub_list_renderer = sub_list_renderer

    async def get_dyn_image(self, dyn_id: str) -> Optional[bytes]:
        cached = await self._dyn_cache_repo.exists(dyn_id)
        if cached:
            dynamic = pickle.loads(cached)
        else:
            dynamic = await self._api.get_dynamic_by_id(dyn_id)
            if dynamic is None:
                return None
            await self._dyn_cache_repo.save(
                dyn_id, dynamic.header.name, pickle.dumps(dynamic)
            )
        return await self._dyn_renderer.render(dynamic)

    async def get_dyn_image_urls(self, dyn_id: str) -> Optional[List[str]]:
        cached = await self._dyn_cache_repo.exists(dyn_id)
        if cached:
            dynamic = pickle.loads(cached)
        else:
            dynamic = await self._api.get_dynamic_by_id(dyn_id)
            if dynamic is None:
                return None
            await self._dyn_cache_repo.save(
                dyn_id, dynamic.header.name, pickle.dumps(dynamic)
            )
        if dynamic.major and dynamic.major.type == "MAJOR_TYPE_OPUS" and dynamic.major.opus:
            return [pic.url for pic in dynamic.major.opus.pics]
        return []

    async def get_sub_list(self, bot_id: int, group_id: int) -> Optional[bytes]:
        data = await self._sub_channel_repo.list_by_group(bot_id, group_id)
        if not data:
            return None
        return await self._sub_list_renderer.render(data)

    async def get_help_image(self) -> str:
        return "https://i0.hdslb.com/bfs/new_dyn/abef945ad1d209ad1d2360624180a15d490040351.png"