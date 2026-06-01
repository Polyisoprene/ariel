from typing import Callable, Awaitable
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from arielbot.application.bot_status_service import BotStatusService
from arielbot.application.query_service import QueryService


def make_bot_status_handler(bot_status_service: BotStatusService, matcher: Matcher, active: bool) -> Callable[[GroupMessageEvent], Awaitable[None]]:
    async def handler(event: GroupMessageEvent) -> None:
        result = await bot_status_service.toggle_push(
            event.self_id, event.group_id, active
        )
        if result is not None:
            await matcher.finish(result)
    return handler


def make_list_handler(query_service: QueryService, matcher: Matcher) -> Callable[[GroupMessageEvent], Awaitable[None]]:
    async def handler(event: GroupMessageEvent) -> None:
        img = await query_service.get_sub_list(event.self_id, event.group_id)
        if img is None:
            await matcher.finish(MessageSegment.text("本群订阅列表为空"))
        await matcher.finish(MessageSegment.image(img))
    return handler


def make_help_handler(query_service: QueryService, matcher: Matcher) -> Callable[[GroupMessageEvent], Awaitable[None]]:
    async def handler(event: GroupMessageEvent) -> None:
        img = await query_service.get_help_image()
        await matcher.finish(MessageSegment.image(img))
    return handler


def make_sd_handler(query_service: QueryService, matcher: Matcher) -> Callable[[Message], Awaitable[None]]:
    async def handler(args: Message = CommandArg()) -> None:
        dyn_id = args.extract_plain_text()
        if not dyn_id or not dyn_id.isdigit():
            return
        img = await query_service.get_dyn_image(dyn_id)
        if img is None:
            return
        await matcher.finish(MessageSegment.image(img))
    return handler


def make_img_handler(query_service: QueryService, matcher: Matcher) -> Callable[[Message], Awaitable[None]]:
    async def handler(args: Message = CommandArg()) -> None:
        dyn_id = args.extract_plain_text()
        if not dyn_id or not dyn_id.isdigit():
            return
        urls = await query_service.get_dyn_image_urls(dyn_id)
        if urls is None:
            return
        if not urls:
            await matcher.finish("此动态没有图片")
            return
        message = MessageSegment.text("")
        for url in urls:
            message += MessageSegment.image(url)
        await matcher.finish(message)
    return handler