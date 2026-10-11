from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler_dishka import setup_dishka
from dishka import AsyncContainer

from app.config import SyncSettings
from app.utils import BUSINESS_TZ
from worker.jobs import (
    cleanup_rate_limiters,
    dispatch_reminders,
    purge_expired_auth,
    purge_sheet_syncs,
    reconcile_chat_access,
    sync_sheets,
)

CHAT_RECONCILE_INTERVAL = 5


# auto_inject: every job run gets its own request scope, so DatabaseProvider commits or rolls back per run.
def create_scheduler(container: AsyncContainer, sync_settings: SyncSettings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=BUSINESS_TZ, job_defaults={"coalesce": True, "max_instances": 1})
    setup_dishka(container=container, scheduler=scheduler, auto_inject=True)
    scheduler.add_job(purge_expired_auth, CronTrigger(hour=4, timezone=BUSINESS_TZ), id="purge_expired_auth")
    scheduler.add_job(cleanup_rate_limiters, IntervalTrigger(minutes=5), id="cleanup_rate_limiters")
    scheduler.add_job(
        sync_sheets,
        IntervalTrigger(minutes=sync_settings.interval_minutes),
        kwargs={"container": container},
        id="sync_sheets",
    )
    scheduler.add_job(
        purge_sheet_syncs,
        CronTrigger(hour=4, minute=30, timezone=BUSINESS_TZ),
        id="purge_sheet_syncs",
    )
    scheduler.add_job(
        dispatch_reminders,
        # At the top of each minute: send_at is whole minutes, so reminders go out on time, not up to a minute late.
        CronTrigger(second=0, timezone=BUSINESS_TZ),
        kwargs={"container": container},
        id="dispatch_reminders",
    )
    scheduler.add_job(
        reconcile_chat_access,
        IntervalTrigger(minutes=CHAT_RECONCILE_INTERVAL),
        kwargs={"container": container},
        id="reconcile_chat_access",
    )
    return scheduler
