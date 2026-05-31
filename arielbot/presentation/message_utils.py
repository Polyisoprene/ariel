from nonebot.adapters.onebot.v11 import MessageSegment


def text(msg: str):
    return MessageSegment.text(msg)


def image(data):
    return MessageSegment.image(data)
