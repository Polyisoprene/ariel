import nonebot
from nonebot.adapters.onebot.v11 import Adapter
from os import path, getcwd

nonebot.init()
nonebot.load_plugin("arielbot.plugins.Core")
nonebot.load_plugins(path.join(getcwd(), "plugins"))
driver = nonebot.get_driver()
driver.register_adapter(Adapter)
app = nonebot.get_asgi()
