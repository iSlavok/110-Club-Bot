from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler_dishka import setup_dishka
from dishka import AsyncContainer

from app.utils import BUSINESS_TZ
from worker.jobs import purge_expired_auth


# auto_inject: every job run gets its own request scope, so DatabaseProvider commits or rolls back per run.
def create_scheduler(container: AsyncContainer) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=BUSINESS_TZ, job_defaults={"coalesce": True, "max_instances": 1})
    setup_dishka(container=container, scheduler=scheduler, auto_inject=True)
    scheduler.add_job(purge_expired_auth, CronTrigger(hour=4, timezone=BUSINESS_TZ), id="purge_expired_auth")
    return scheduler
