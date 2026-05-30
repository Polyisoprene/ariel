from nonebot import on_command
from nonebot.adapters import Bot, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from arielbot.presentation.middleware import make_bot_is_active_rule


class CommandRegistry:
    _matchers = {}

    @classmethod
    def register(cls, name: str, handler, *,
                 permission=None, aliases=None, rule=None) -> None:
        matcher = on_command(name, permission=permission,
                             aliases=aliases, rule=rule)
        cls._matchers[name] = matcher
        return matcher

    @classmethod
    def register_all(cls, services, container) -> None:
        bot_is_active = make_bot_is_active_rule(container.bot_repo)

        # login
        login_matcher = cls.register(
            "login", None, permission=SUPERUSER, aliases={"登录"}
        )
        @login_matcher.handle()
        async def _(bot: Bot, event: GroupMessageEvent):
            from arielbot.presentation.commands.auth_commands import make_login_handler
            handler = make_login_handler(services.auth_service)
            await handler(bot, event)
            await login_matcher.finish()

        # sub
        sub_matcher = cls.register(
            "sub", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active, aliases={"订阅"},
        )
        @sub_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            from arielbot.presentation.commands.sub_commands import make_sub_handler
            handler = make_sub_handler(services.sub_service, sub_matcher)
            await handler(event, args)

        # unsub
        unsub_matcher = cls.register(
            "unsub", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active, aliases={"删除"},
        )
        @unsub_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            from arielbot.presentation.commands.sub_commands import make_unsub_handler
            handler = make_unsub_handler(services.sub_service, unsub_matcher)
            await handler(event, args)

        # live_on
        live_on_matcher = cls.register(
            "live_on", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active,
        )
        @live_on_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            from arielbot.presentation.commands.sub_commands import make_live_toggle_handler
            handler = make_live_toggle_handler(services.sub_service, live_on_matcher, True)
            await handler(event, args)

        # live_off
        live_off_matcher = cls.register(
            "live_off", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active,
        )
        @live_off_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            from arielbot.presentation.commands.sub_commands import make_live_toggle_handler
            handler = make_live_toggle_handler(services.sub_service, live_off_matcher, False)
            await handler(event, args)

        # dyn_on
        dyn_on_matcher = cls.register(
            "dyn_on", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active,
        )
        @dyn_on_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            from arielbot.presentation.commands.sub_commands import make_dyn_toggle_handler
            handler = make_dyn_toggle_handler(services.sub_service, dyn_on_matcher, True)
            await handler(event, args)

        # dyn_off
        dyn_off_matcher = cls.register(
            "dyn_off", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
            rule=bot_is_active,
        )
        @dyn_off_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            from arielbot.presentation.commands.sub_commands import make_dyn_toggle_handler
            handler = make_dyn_toggle_handler(services.sub_service, dyn_off_matcher, False)
            await handler(event, args)

        # bot_on
        bot_on_matcher = cls.register(
            "bot_on", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
        )
        @bot_on_matcher.handle()
        async def _(event: GroupMessageEvent):
            from arielbot.presentation.commands.query_commands import make_bot_status_handler
            handler = make_bot_status_handler(services.bot_status_service, bot_on_matcher, True)
            await handler(event)

        # bot_off
        bot_off_matcher = cls.register(
            "bot_off", None,
            permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
        )
        @bot_off_matcher.handle()
        async def _(event: GroupMessageEvent):
            from arielbot.presentation.commands.query_commands import make_bot_status_handler
            handler = make_bot_status_handler(services.bot_status_service, bot_off_matcher, False)
            await handler(event)

        # list
        list_matcher = cls.register(
            "list", None, rule=bot_is_active, aliases={"列表"},
        )
        @list_matcher.handle()
        async def _(event: GroupMessageEvent):
            from arielbot.presentation.commands.query_commands import make_list_handler
            handler = make_list_handler(services.query_service, list_matcher)
            await handler(event)

        # help
        help_matcher = cls.register("help", None)
        @help_matcher.handle()
        async def _():
            from arielbot.presentation.commands.query_commands import make_help_handler
            handler = make_help_handler(services.query_service, help_matcher)
            await handler()

        # sd
        sd_matcher = cls.register("sd", None)
        @sd_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            from arielbot.presentation.commands.query_commands import make_sd_handler
            handler = make_sd_handler(services.query_service, sd_matcher)
            await handler(args)

        # img
        img_matcher = cls.register("img", None)
        @img_matcher.handle()
        async def _(event: GroupMessageEvent, args: Message = CommandArg()):
            from arielbot.presentation.commands.query_commands import make_img_handler
            handler = make_img_handler(services.query_service, img_matcher)
            await handler(args)