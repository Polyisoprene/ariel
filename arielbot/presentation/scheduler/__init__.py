def register_scheduled_jobs(scheduler, dyn_check_job, live_check_job):
    @scheduler.scheduled_job("cron", second="*/8", id="dyn_pusher", max_instances=1)
    async def _():
        await dyn_check_job.run()

    @scheduler.scheduled_job("cron", second="*/10", id="live_pusher", max_instances=1)
    async def _():
        await live_check_job.run()