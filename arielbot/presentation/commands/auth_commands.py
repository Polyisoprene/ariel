from typing import Callable, Awaitable
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from arielbot.application.auth_service import AuthService


def make_login_handler(auth_service: AuthService) -> Callable[[Bot, GroupMessageEvent], Awaitable[None]]:
    async def handler(bot: Bot, event: GroupMessageEvent) -> None:
        await auth_service.login(bot, event)
    return handler