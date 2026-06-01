from typing import Callable, Awaitable
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.adapters import Bot
from nonebot.drivers import Driver
from arielbot.domain.events import BotConnected, BotDisconnected, BotShutdown
from arielbot.domain.interfaces.event_bus import EventBus
from arielbot.application.bot_status_service import BotStatusService


def make_bot_is_active_rule(bot_status_service: BotStatusService) -> Callable[[GroupMessageEvent], Awaitable[bool]]:
    async def bot_is_active(event: GroupMessageEvent) -> bool:
        return await bot_status_service.is_bot_active(event.self_id, event.group_id)
    return bot_is_active


def register_lifecycle_hooks(driver: Driver, event_bus: EventBus) -> None:
    @driver.on_bot_connect
    async def _(bot: Bot) -> None:
        await event_bus.publish(BotConnected(bot.self_id))

    @driver.on_bot_disconnect
    async def _(bot: Bot) -> None:
        await event_bus.publish(BotDisconnected(bot.self_id))

    @driver.on_shutdown
    async def _() -> None:
        await event_bus.publish(BotShutdown())