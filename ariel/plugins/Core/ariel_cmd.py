from nonebot import on_command
from nonebot.adapters import Bot
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN
from nonebot.adapters.onebot.v11 import GROUP_OWNER
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from ariel_tools import *

from ariel_tools import LoginTools
from ariel_rule import bot_is_active

login = on_command("login", aliases={"登录"}, permission=SUPERUSER, priority=3, block=True)

add_sub = on_command("sub", rule=bot_is_active, aliases={"订阅"}, permission=SUPERUSER|GROUP_ADMIN|GROUP_OWNER, priority=10, block=True)
del_sub = on_command("unsub",  rule=bot_is_active, aliases={"删除"}, permission=SUPERUSER|GROUP_ADMIN|GROUP_OWNER, priority=10, block=True)
sub_list = on_command("list",  rule=bot_is_active, aliases={"列表"}, priority=10, block=True)

live_active = on_command("live_on", rule=bot_is_active, permission=SUPERUSER|GROUP_ADMIN|GROUP_OWNER, priority=10, block=True)
live_deactivate = on_command("live_off", rule=bot_is_active, permission=SUPERUSER|GROUP_ADMIN|GROUP_OWNER, priority=10, block=True)

dyn_active = on_command("dyn_on", rule=bot_is_active, permission=SUPERUSER|GROUP_ADMIN|GROUP_OWNER, priority=10, block=True)
dyn_deactivate = on_command("dyn_off", rule=bot_is_active, permission=SUPERUSER|GROUP_ADMIN|GROUP_OWNER, priority=10, block=True)

bot_active = on_command("bot_on", permission=SUPERUSER|GROUP_ADMIN|GROUP_OWNER, priority=10, block=True)
bot_deactivate = on_command("bot_off", permission=SUPERUSER|GROUP_ADMIN|GROUP_OWNER, priority=10, block=True)


@login.handle()
async def _(bot:Bot,event:GroupMessageEvent):
    login_handler = LoginTools()
    await login_handler.login_handle(bot, event)
    await login.finish()

@add_sub.handle()
async def _(event:GroupMessageEvent, args: Message = CommandArg()):
    if args.extract_plain_text() and args.extract_plain_text().isdigit():
        add_sub_processor = AddSubTools(args.extract_plain_text())
        result = await add_sub_processor.add_sub_processor(event)
        await add_sub.finish(result)
    else:
        await add_sub.finish("请携带正确的uid后重试")

@del_sub.handle()
async def _(event:GroupMessageEvent, args: Message = CommandArg()):
    if args.extract_plain_text() and args.extract_plain_text().isdigit():
        del_sub_processor = DelSubTools(args.extract_plain_text())
        result = await del_sub_processor.del_sub_processor(event)
        await del_sub.finish(result)
    else:
        await del_sub.finish("请携带正确的uid后重试")


@live_active.handle()
async def _(event:GroupMessageEvent, args: Message = CommandArg()):
    if args.extract_plain_text() and args.extract_plain_text().isdigit():
        live_active_processor = UpdataSubTools(args.extract_plain_text())
        result = await live_active_processor.update_sub_handler(event,1)
        await live_active.finish(result)
    else:
        await live_active.finish("请携带正确的uid后重试")
    
@live_deactivate.handle()
async def _(event:GroupMessageEvent, args: Message = CommandArg()):
    if args.extract_plain_text() and args.extract_plain_text().isdigit():
        live_deactivate_processor = UpdataSubTools(args.extract_plain_text())
        result = await live_deactivate_processor.update_sub_handler(event,0)
        await live_deactivate.finish(result)
    else:
        await live_deactivate.finish("请携带正确的uid后重试")

@dyn_active.handle()
async def _(event:GroupMessageEvent, args: Message = CommandArg()):
    if args.extract_plain_text() and args.extract_plain_text().isdigit():
        dyn_active_processor = UpdataSubTools(args.extract_plain_text())
        result = await dyn_active_processor.update_sub_handler(event,dyn_active=1)
        await dyn_active.finish(result)
    else:
        await dyn_active.finish("请携带正确的uid后重试")
        
@dyn_deactivate.handle()
async def _(event:GroupMessageEvent, args: Message = CommandArg()):
    if args.extract_plain_text() and args.extract_plain_text().isdigit():
        dyn_deactivate_processor = UpdataSubTools(args.extract_plain_text())
        result = await dyn_deactivate_processor.update_sub_handler(event,dyn_active=0)
        await dyn_deactivate.finish(result)
    else:
        await dyn_deactivate.finish("请携带正确的uid后重试")

