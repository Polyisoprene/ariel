from arielbot.domain.events import DynamicDetected, LiveStatusChanged
from arielbot.domain.events import BotConnected, BotDisconnected, BotShutdown
from arielbot.infrastructure.adapters.bot_client import BotClient


class DynPushHandler:
    def __init__(self, bot_client: BotClient):
        self._client = bot_client

    async def handle(self, event: DynamicDetected):
        for gid, bid in event.targets:
            message = (
                f"{event.uname}发布了新动态:\n\n"
                f"传送门→https://t.bilibili.com/{event.dyn_id}"
            )
            await self._client.send_group_msg(
                gid, bid, message, image=event.rendered_image
            )


class LivePushHandler:
    def __init__(self, bot_client: BotClient):
        self._client = bot_client

    async def handle(self, event: LiveStatusChanged):
        if not event.is_live:
            return
        for gid, bid in event.targets:
            message = (
                f"【{event.uname}】开播啦!!!\n\n"
                f"标题：{event.title}\n\n"
                f"传送门：https://live.bilibili.com/{event.room_id}"
            )
            await self._client.send_group_msg(
                gid, bid, message, cover=event.cover_url
            )


class BotLifecycleHandler:
    def __init__(self, bot_status_service):
        self._service = bot_status_service

    async def on_connect(self, event: BotConnected):
        await self._service.on_bot_connect(event.bot_id)

    async def on_disconnect(self, event: BotDisconnected):
        await self._service.on_bot_disconnect(event.bot_id)

    async def on_shutdown(self, event: BotShutdown):
        await self._service.shutdown_all()