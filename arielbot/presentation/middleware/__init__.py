from nonebot.adapters.onebot.v11 import GroupMessageEvent
from arielbot.domain.events import BotConnected, BotDisconnected, BotShutdown


def make_bot_is_active_rule(bot_repo):
    async def bot_is_active(event: GroupMessageEvent) -> bool:
        status = await bot_repo.get(event.self_id, event.group_id)
        if not status:
            await bot_repo.save(event.self_id, event.group_id, 1, 1)
            return True
        return bool(status[0] and status[1])
    return bot_is_active


def register_lifecycle_hooks(driver, event_bus):
    @driver.on_bot_connect
    async def _(bot):
        await event_bus.publish(BotConnected(bot.self_id))

    @driver.on_bot_disconnect
    async def _(bot):
        await event_bus.publish(BotDisconnected(bot.self_id))

    @driver.on_shutdown
    async def _():
        await event_bus.publish(BotShutdown())