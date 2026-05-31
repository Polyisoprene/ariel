from typing import Optional
from arielbot.domain.interfaces.repository import BotStatusRepository
from arielbot.domain.interfaces.event_bus import EventBus


class BotStatusService:
    def __init__(self, bot_repo: BotStatusRepository, event_bus: EventBus):
        self._repo = bot_repo
        self._bus = event_bus

    async def toggle_push(self, bot_id: int, group_id: int, active: bool) -> Optional[str]:
        result = await self._repo.get(bot_id, group_id)
        if not result:
            await self._repo.save(bot_id, group_id, int(active), 1)
            return "bot已开启" if active else "bot已关闭"
        if int(active) == result[0]:
            if not active:
                return "bot已经为关闭状态"
            return "bot已经为开启状态"
        await self._repo.update_push(bot_id, group_id, int(active))
        return "bot关闭成功" if not active else "bot开启成功"

    async def is_bot_active(self, bot_id: int, group_id: int) -> bool:
        status = await self._repo.get(bot_id, group_id)
        if not status:
            await self._repo.save(bot_id, group_id, 1, 1)
            return True
        return bool(status[0] and status[1])

    async def on_bot_connect(self, bot_id: int) -> None:
        await self._repo.update_active(bot_id, 1)

    async def on_bot_disconnect(self, bot_id: int) -> None:
        await self._repo.update_active(bot_id, 0)

    async def shutdown_all(self) -> None:
        bots = await self._repo.list_all_bots()
        for bid in bots:
            await self._repo.update_active(bid, 0)