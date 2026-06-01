from apscheduler.schedulers.asyncio import AsyncIOScheduler
from arielbot.application.push.check_jobs import DynCheckJob, LiveCheckJob
from arielbot.domain.interfaces.repository import DynCacheRepository


def register_scheduled_jobs(scheduler: AsyncIOScheduler, dyn_check_job: DynCheckJob, live_check_job: LiveCheckJob, dyn_cache_repo: DynCacheRepository) -> None:
    @scheduler.scheduled_job("cron", second="*/8", id="dyn_pusher", max_instances=1)
    async def _() -> None:
        await dyn_check_job.run()

    @scheduler.scheduled_job("cron", second="*/10", id="live_pusher", max_instances=1)
    async def _() -> None:
        await live_check_job.run()

    @scheduler.scheduled_job("cron", hour="3", id="dyn_archive", max_instances=1)
    async def _() -> None:
        await dyn_cache_repo.archive_old_dynamics(7)