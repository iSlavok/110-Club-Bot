import asyncio

from apscheduler.triggers.cron import CronTrigger
from dishka import FromDishka

from app.services import UserService
from worker import create_scheduler


async def test_auth_cleanup_runs_nightly(container) -> None:
    scheduler = create_scheduler(container)

    job = scheduler.get_job("purge_expired_auth")

    assert job is not None
    assert isinstance(job.trigger, CronTrigger)
    assert str(job.trigger.fields[job.trigger.FIELD_NAMES.index("hour")]) == "4"


async def test_each_job_run_gets_its_own_request_scope(container) -> None:
    scheduler = create_scheduler(container)
    received: list[UserService] = []
    both_ran = asyncio.Event()

    async def job(user_service: FromDishka[UserService]) -> None:
        received.append(user_service)
        if len(received) == 2:
            both_ran.set()

    scheduler.start()
    try:
        scheduler.add_job(job)
        scheduler.add_job(job)
        await asyncio.wait_for(both_ran.wait(), timeout=5)
    finally:
        scheduler.shutdown(wait=False)

    assert received[0] is not received[1]
