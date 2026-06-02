import asyncio
import os
import pickle
from typing import List, Optional
from arielbot.domain.interfaces.api import BiliContentAPI
from arielbot.domain.interfaces.repository import DynCacheRepository, SubChannelRepository
from arielbot.domain.interfaces.renderer import DynRenderer, SubListRenderer, HelpRenderer

_HELP_CACHE_PATH = os.path.join(os.getcwd(), "data", "help.png")


class QueryService:
    def __init__(self, content_api: BiliContentAPI,
                 dyn_cache_repo: DynCacheRepository,
                 sub_channel_repo: SubChannelRepository,
                 dyn_renderer: DynRenderer,
                 sub_list_renderer: SubListRenderer,
                 help_renderer: HelpRenderer):
        self._api = content_api
        self._dyn_cache_repo = dyn_cache_repo
        self._sub_channel_repo = sub_channel_repo
        self._dyn_renderer = dyn_renderer
        self._sub_list_renderer = sub_list_renderer
        self._help_renderer = help_renderer

    async def _get_or_fetch_dynamic(self, dyn_id: str) -> Optional[object]:
        cached = await self._dyn_cache_repo.find(dyn_id)
        if cached:
            return pickle.loads(cached)
        dynamic = await self._api.get_dynamic_by_id(dyn_id)
        if dynamic is None:
            return None
        await self._dyn_cache_repo.save(
            dyn_id, dynamic.header.name, pickle.dumps(dynamic)
        )
        return dynamic

    async def get_dyn_image(self, dyn_id: str) -> Optional[bytes]:
        dynamic = await self._get_or_fetch_dynamic(dyn_id)
        if dynamic is None:
            return None
        return await self._dyn_renderer.render(dynamic)

    async def get_dyn_image_urls(self, dyn_id: str) -> Optional[List[str]]:
        dynamic = await self._get_or_fetch_dynamic(dyn_id)
        if dynamic is None:
            return None
        if dynamic.major and dynamic.major.type == "MAJOR_TYPE_OPUS" and dynamic.major.opus:
            return [pic.url for pic in dynamic.major.opus.pics]
        return []

    async def get_sub_list(self, bot_id: int, group_id: int) -> Optional[bytes]:
        data = await self._sub_channel_repo.list_by_group(bot_id, group_id)
        if not data:
            return None
        return await self._sub_list_renderer.render(data)

    async def get_help_image(self) -> bytes:
        loop = asyncio.get_running_loop()
        exists = await loop.run_in_executor(None, os.path.exists, _HELP_CACHE_PATH)
        if exists:
            return await loop.run_in_executor(None, _read_help_cache)
        await loop.run_in_executor(None, _ensure_help_dir)
        img_bytes = await self._help_renderer.render()
        await loop.run_in_executor(None, _write_help_cache, img_bytes)
        return img_bytes


def _ensure_help_dir() -> None:
    os.makedirs(os.path.dirname(_HELP_CACHE_PATH), exist_ok=True)


def _read_help_cache() -> bytes:
    with open(_HELP_CACHE_PATH, "rb") as f:
        return f.read()


def _write_help_cache(data: bytes) -> None:
    with open(_HELP_CACHE_PATH, "wb") as f:
        f.write(data)
