from nonebot import on_command
from nonebot.adapters import Bot, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from arielbot.presentation.middleware import make_bot_is_active_rule
from arielbot.presentation.commands.auth_commands import make_login_handler
from arielbot.presentation.commands.sub_commands import (
    make_sub_handler,
    make_unsub_handler,
    make_live_toggle_handler,
    make_dyn_toggle_handler,
)
from arielbot.presentation.commands.query_commands import (
    make_bot_status_handler,
    make_list_handler,
    make_help_handler,
    make_sd_handler,
    make_img_handler,
)


class CommandRegistry:
    _matchers = {}

    @classmethod
    def register(cls, name: str, *,
                 permission=None, aliases=None, rule=None):
        matcher = on_command(name, permission=permission,
                             aliases=aliases, rule=rule)
        cls._matchers[name] = matcher
        return matcher

    @classmethod
    def register_all(cls, container) -> None:
        bot_is_active = make_bot_is_active_rule(container.bot_status_service)

        login_matcher = cls.register(
            "login", permission=SUPERUSER, aliases={"登录"}
        )
        @login_matcher.handle()
        async def _(bot: Bot, event: GroupMessageEvent):
            handler = make_login_handler(container.auth_service)
            await handler(bot, event)
            await login_matcher.finish()

        sub_matcher = cls.register(
            "sub",
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active, aliases={"订阅"},
        )
        @sub_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            handler = make_sub_handler(container.sub_service, sub_matcher)
            await handler(event, args)

        unsub_matcher = cls.register(
            "unsub", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active, aliases={"删除"},
        )
        @unsub_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            handler = make_unsub_handler(container.sub_service, unsub_matcher)
            await handler(event, args)

        live_on_matcher = cls.register(
            "live_on", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active,
        )
        @live_on_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            handler = make_live_toggle_handler(container.sub_service, live_on_matcher, True)
            await handler(event, args)

        live_off_matcher = cls.register(
            "live_off", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active,
        )
        @live_off_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            handler = make_live_toggle_handler(container.sub_service, live_off_matcher, False)
            await handler(event, args)

        dyn_on_matcher = cls.register(
            "dyn_on", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active,
        )
        @dyn_on_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            handler = make_dyn_toggle_handler(container.sub_service, dyn_on_matcher, True)
            await handler(event, args)

        dyn_off_matcher = cls.register(
            "dyn_off", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active,
        )
        @dyn_off_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            handler = make_dyn_toggle_handler(container.sub_service, dyn_off_matcher, False)
            await handler(event, args)

        bot_on_matcher = cls.register(
            "bot_on", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
        )
        @bot_on_matcher.handle()
        async def _(event: GroupMessageEvent):
            handler = make_bot_status_handler(container.bot_status_service, bot_on_matcher, True)
            await handler(event)

        bot_off_matcher = cls.register(
            "bot_off", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
        )
        @bot_off_matcher.handle()
        async def _(event: GroupMessageEvent):
            handler = make_bot_status_handler(container.bot_status_service, bot_off_matcher, False)
            await handler(event)

        list_matcher = cls.register(
            "list", None, rule=bot_is_active, aliases={"列表"},
        )
        @list_matcher.handle()
        async def _(event: GroupMessageEvent):
            handler = make_list_handler(container.query_service, list_matcher)
            await handler(event)

        help_matcher = cls.register("help")
        @help_matcher.handle()
        async def _(event: GroupMessageEvent):
            handler = make_help_handler(container.query_service, help_matcher)
            await handler(event)

        sd_matcher = cls.register("sd")
        @sd_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            handler = make_sd_handler(container.query_service, sd_matcher)
            await handler(args)

        img_matcher = cls.register("img")
        @img_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            handler = make_img_handler(container.query_service, img_matcher)
            await handler(args)