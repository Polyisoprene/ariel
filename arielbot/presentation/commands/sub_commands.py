from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import GroupMessageEvent


def make_sub_handler(sub_service, matcher):
    async def handler(event: GroupMessageEvent, args: Message = CommandArg()):
        uid = args.extract_plain_text()
        if not uid or not uid.isdigit():
            await matcher.finish("请携带正确的uid后重试")
        result = await sub_service.add_sub(uid, event.group_id, event.self_id)
        await matcher.finish(result)
    return handler


def make_unsub_handler(sub_service, matcher):
    async def handler(event: GroupMessageEvent, args: Message = CommandArg()):
        uid = args.extract_plain_text()
        if not uid or not uid.isdigit():
            await matcher.finish("请携带正确的uid后重试")
        result = await sub_service.del_sub(uid, event.group_id, event.self_id)
        await matcher.finish(result)
    return handler


def make_live_toggle_handler(sub_service, matcher, active: bool):
    async def handler(event: GroupMessageEvent, args: Message = CommandArg()):
        uid = args.extract_plain_text()
        if not uid or not uid.isdigit():
            await matcher.finish("请携带正确的uid后重试")
        result = await sub_service.toggle_live(
            uid, event.group_id, event.self_id, active
        )
        await matcher.finish(result)
    return handler


def make_dyn_toggle_handler(sub_service, matcher, active: bool):
    async def handler(event: GroupMessageEvent, args: Message = CommandArg()):
        uid = args.extract_plain_text()
        if not uid or not uid.isdigit():
            await matcher.finish("请携带正确的uid后重试")
        result = await sub_service.toggle_dyn(
            uid, event.group_id, event.self_id, active
        )
        await matcher.finish(result)
    return handler