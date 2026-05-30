from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot, MessageSegment


class BotClient:
    async def send_group_msg(self, group_id: int, bot_id: int,
                              text: str = "", image: bytes = None,
                              cover: str = None) -> None:
        bot: Bot = get_bot(str(bot_id))
        message = MessageSegment.text(text)
        if image:
            message += MessageSegment.image(image)
        if cover:
            message += MessageSegment.image(cover)
        await bot.send_group_msg(group_id=group_id, message=message)