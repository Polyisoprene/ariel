from arielbot.plugins.Core.ariel_database import DataManager
from nonebot.adapters.onebot.v11 import GroupMessageEvent


async def bot_is_active(event:GroupMessageEvent) -> bool:
    async with DataManager() as m:
        result = await m.select_bot_status((event.self_id,event.group_id))
        if not result:
            await m.insert_bot_status((event.self_id,event.group_id,1,1))
            return True
        return (result[0] and result[1])