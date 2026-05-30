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
                 sub_channel_repo: SubChannelRepository,
                 dyn_renderer: DynRenderer,
                 event_bus: EventBus):
        self._api = content_api
        self._dyn_cache_repo = dyn_cache_repo
        self._sub_channel_repo = sub_channel_repo
        self._dyn_renderer = dyn_renderer
        self._event_bus = event_bus

    async def run(self):
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
            await self._dyn_cache_repo.save(
                dynamic.message_id, dynamic.header.name, pickle.dumps(dynamic)
            )
            if not targets:
                logger.info("没有需要推送的群，跳过该动态")
                continue
            rendered = await self._dyn_renderer.render(dynamic)
            await self._event_bus.publish(DynamicDetected(
                dynamic=dynamic,
                dyn_id=dynamic.message_id,
                uname=dynamic.header.name,
                targets=targets,
                rendered_image=rendered,
            ))


class LiveCheckJob:
    def __init__(self, content_api: BiliContentAPI,
                 sub_target_repo: SubTargetRepository,
                 sub_channel_repo: SubChannelRepository,
                 event_bus: EventBus):
        self._api = content_api
        self._target_repo = sub_target_repo
        self._channel_repo = sub_channel_repo
        self._event_bus = event_bus

    async def run(self):
        all_check_uid_list = await self._channel_repo.find_live_check_uids()
        if not all_check_uid_list:
            return
        all_live_status = {f"{row[0]}": row[1] for row in all_check_uid_list}
        uid_list = [row[0] for row in all_check_uid_list]
        check_result = await self._api.get_room_info_by_uids(uid_list)
        if check_result is None:
            return
        for k, v in check_result.items():
            if v["live_status"] != 1:
                v["live_status"] = 0
            if all_live_status.get(k) == v["live_status"]:
                continue
            if all_live_status.get(k) == 1:
                await self._target_repo.update(v["uname"], 0, v["uid"])
                continue
            await self._target_repo.update(v["uname"], 1, v["uid"])
            targets = await self._channel_repo.find_push_targets_for_live(v["uid"])
            if not targets:
                continue
            await self._event_bus.publish(LiveStatusChanged(
                uid=v["uid"],
                uname=v["uname"],
                room_id=v["room_id"],
                title=v["title"],
                cover_url=v["cover_from_user"],
                is_live=(v["live_status"] == 1),
                targets=targets,
            ))