from typing import Optional
from nonebot import get_bot, logger
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from arielbot.domain.interfaces.bot_client import BotClient as BotClientABC


class BotClient(BotClientABC):
    async def send_group_msg(self, group_id: int, bot_id: int,
                              text: str = "", image: Optional[bytes] = None,
                              cover: Optional[str] = None) -> None:
        try:
            bot: Bot = get_bot(str(bot_id))
        except KeyError:
            logger.warning(f"Bot {bot_id} not connected, skip sending message to group {group_id}")
            return
        message = MessageSegment.text(text)
        if image:
            message += MessageSegment.image(image)
        if cover:
            message += MessageSegment.image(cover)
        await bot.send_group_msg(group_id=group_id, message=message)