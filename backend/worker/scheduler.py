from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dishka import AsyncContainer

from app.utils import BUSINESS_TZ


def create_scheduler(container: AsyncContainer) -> AsyncIOScheduler:  # noqa: ARG001 - jobs are registered per feature
    return AsyncIOScheduler(timezone=BUSINESS_TZ, job_defaults={"coalesce": True, "max_instances": 1})
