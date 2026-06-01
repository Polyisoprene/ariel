import pickle
from nonebot import logger
from arielbot.domain.events import DynamicDetected, LiveStatusChanged
from arielbot.domain.interfaces.api import BiliContentAPI
from arielbot.domain.interfaces.repository import (
    DynCacheRepository,
    SubTargetRepository,
    SubChannelRepository,
)
from arielbot.domain.interfaces.renderer import DynRenderer
from arielbot.domain.interfaces.event_bus import EventBus


class DynCheckJob:
    def __init__(self, content_api: BiliContentAPI,
                 dyn_cache_repo: DynCacheRepository,
                 sub_target_repo: SubTargetRepository,
                 sub_channel_repo: SubChannelRepository,
                 dyn_renderer: DynRenderer,
                 event_bus: EventBus):
        self._api = content_api
        self._dyn_cache_repo = dyn_cache_repo
        self._target_repo = sub_target_repo
        self._sub_channel_repo = sub_channel_repo
        self._dyn_renderer = dyn_renderer
        self._event_bus = event_bus

    async def run(self) -> None:
        follow_dynamic_list = await self._api.get_follow_dynamics()
        if follow_dynamic_list is None:
            return
        for dynamic in follow_dynamic_list:
            cached = await self._dyn_cache_repo.exists(dynamic.message_id)
            if cached:
                continue
            logger.info(
                f"检测到{dynamic.header.name}的新动态: {dynamic.message_id}"
            )
            targets = await self._sub_channel_repo.find_push_targets_for_dyn(
                dynamic.header.mid
            )
            if not targets:
                logger.info("没有需要推送的群，跳过该动态")
                await self._dyn_cache_repo.save(
                    dynamic.message_id, dynamic.header.name, pickle.dumps(dynamic)
                )
                await self._target_repo.update(
                    dynamic.header.name, dynamic.header.mid
                )
                continue
            rendered = await self._dyn_renderer.render(dynamic)
            await self._dyn_cache_repo.save(
                dynamic.message_id, dynamic.header.name, pickle.dumps(dynamic)
            )
            await self._target_repo.update(
                dynamic.header.name, dynamic.header.mid
            )
            await self._event_bus.publish(DynamicDetected(
                dynamic=dynamic,
                dyn_id=dynamic.message_id,
                uname=dynamic.header.name,
                targets=targets,
                rendered_image=rendered,
            ))


class LiveCheckJob:
    def __init__(self, content_api: BiliContentAPI,
                 sub_channel_repo: SubChannelRepository,
                 event_bus: EventBus):
        self._api = content_api
        self._channel_repo = sub_channel_repo
        self._event_bus = event_bus
        self._live_cache: dict[str, int] = {}

    async def run(self) -> None:
        uid_list = await self._channel_repo.find_all_subscribed_uids()
        if not uid_list:
            return
        check_result = await self._api.get_room_info_by_uids(uid_list)
        if check_result is None:
            return
        for k, v in check_result.items():
            current = 1 if v["live_status"] == 1 else 0
            prev = self._live_cache.get(k, current)
            self._live_cache[k] = current
            if prev == current:
                continue
            if prev == 1:
                continue
            targets = await self._channel_repo.find_push_targets_for_live(str(v["uid"]))
            if not targets:
                continue
            await self._event_bus.publish(LiveStatusChanged(
                uid=str(v["uid"]),
                uname=v["uname"],
                room_id=v["room_id"],
                title=v["title"],
                cover_url=v["cover_from_user"],
                is_live=(current == 1),
                targets=targets,
            ))
