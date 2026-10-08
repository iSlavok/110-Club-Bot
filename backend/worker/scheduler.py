from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dishka import AsyncContainer

from app.utils import BUSINESS_TZ
from worker.injection import inject_job
from worker.jobs import purge_expired_auth


def create_scheduler(container: AsyncContainer) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=BUSINESS_TZ, job_defaults={"coalesce": True, "max_instances": 1})
    scheduler.add_job(
        inject_job(container, purge_expired_auth),
        CronTrigger(hour=4, timezone=BUSINESS_TZ),
        id="purge_expired_auth",
    )
    return scheduler
