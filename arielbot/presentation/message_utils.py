from typing import Union
from nonebot.adapters.onebot.v11 import MessageSegment


def text(msg: str) -> MessageSegment:
    return MessageSegment.text(msg)


def image(data: Union[bytes, str]) -> MessageSegment:
    return MessageSegment.image(data)
