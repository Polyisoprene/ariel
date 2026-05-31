from nonebot import get_driver, require

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from arielbot.infrastructure.container import Container
from arielbot.presentation.commands.registry import CommandRegistry
from arielbot.presentation.scheduler import register_scheduled_jobs
from arielbot.presentation.middleware import register_lifecycle_hooks

driver = get_driver()

container = Container()
register_lifecycle_hooks(driver, container.event_bus)
CommandRegistry.register_all(container)
register_scheduled_jobs(scheduler, container.dyn_check_job, container.live_check_job)


@driver.on_startup
async def _():
    await container.event_bus.start()


@driver.on_shutdown
async def _():
    await container.event_bus.stop()