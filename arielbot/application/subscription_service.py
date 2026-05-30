from arielbot.domain.interfaces.api import BiliContentAPI
from arielbot.domain.interfaces.repository import SubTargetRepository, SubChannelRepository


class SubscriptionService:
    def __init__(self, content_api: BiliContentAPI,
                 target_repo: SubTargetRepository,
                 channel_repo: SubChannelRepository):
        self._api = content_api
        self._target_repo = target_repo
        self._channel_repo = channel_repo

    async def add_sub(self, uid: str, group_id: int, bot_id: int) -> str:
        check_has_sub = await self._target_repo.get(uid)
        if check_has_sub:
            check_in_group = await self._channel_repo.get(uid, group_id, bot_id)
            if check_in_group:
                if check_in_group[0] == 0 or check_in_group[1] == 0:
                    await self._channel_repo.update(1, 1, uid, group_id, bot_id)
                    return f"成功添加订阅 --> {check_has_sub[0]}({uid})"
                else:
                    return f"本群已订阅过 --> {check_has_sub[0]}({uid})"
            else:
                await self._channel_repo.save(uid, group_id, bot_id)
                return f"成功添加订阅 --> {check_has_sub[0]}({uid})"
        else:
            uid_info = await self._api.get_user_info(uid)
            if isinstance(uid_info, str):
                return uid_info
            if uid_info.get("following") != True:
                follow_result = await self._api.follow_user(uid, 1)
                if not follow_result:
                    return "添加订阅失败"
            await self._target_repo.save(uid, uid_info["card"]["name"], 0)
            await self._channel_repo.save(uid, group_id, bot_id)
            return f"成功添加订阅 --> {uid_info['card']['name']}({uid})"

    async def del_sub(self, uid: str, group_id: int, bot_id: int) -> str:
        check_in_group = await self._channel_repo.get(uid, group_id, bot_id)
        if not check_in_group:
            return f"本群没有订阅 --> {uid}"
        await self._channel_repo.update(0, 0, uid, group_id, bot_id)
        uid_info = await self._target_repo.get(uid)
        return f"成功删除订阅 --> {uid_info[0]}({uid})"

    async def toggle_live(self, uid: str, group_id: int, bot_id: int, active: bool) -> str:
        check_in_group = await self._channel_repo.get(uid, group_id, bot_id)
        if not check_in_group:
            return f"本群没有订阅 --> {uid}"
        await self._channel_repo.update(
            int(active), check_in_group[1], uid, group_id, bot_id
        )
        return "开启直播推送成功" if active else "关闭直播推送成功"

    async def toggle_dyn(self, uid: str, group_id: int, bot_id: int, active: bool) -> str:
        check_in_group = await self._channel_repo.get(uid, group_id, bot_id)
        if not check_in_group:
            return f"本群没有订阅 --> {uid}"
        await self._channel_repo.update(
            check_in_group[0], int(active), uid, group_id, bot_id
        )
        return "开启动态推送成功" if active else "关闭动态推送成功"