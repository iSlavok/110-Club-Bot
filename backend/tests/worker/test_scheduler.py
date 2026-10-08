import asyncio
from datetime import UTC, datetime, timedelta

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from dishka import FromDishka

from app.config import SyncSettings
from app.services import UserService
from tests.factories import make_club
from worker import create_scheduler


async def test_auth_cleanup_runs_nightly(container) -> None:
    scheduler = create_scheduler(container, SyncSettings())

    job = scheduler.get_job("purge_expired_auth")

    assert job is not None
    assert isinstance(job.trigger, CronTrigger)
    assert str(job.trigger.fields[job.trigger.FIELD_NAMES.index("hour")]) == "4"


async def test_rate_limiter_cleanup_runs_every_five_minutes(container) -> None:
    scheduler = create_scheduler(container, SyncSettings())

    job = scheduler.get_job("cleanup_rate_limiters")

    assert job is not None
    assert isinstance(job.trigger, IntervalTrigger)
    assert job.trigger.interval == timedelta(minutes=5)


async def test_sheets_sync_runs_on_configured_interval_with_app_container(container) -> None:
    scheduler = create_scheduler(container, SyncSettings(interval_minutes=7))

    job = scheduler.get_job("sync_sheets")

    assert job is not None
    assert isinstance(job.trigger, IntervalTrigger)
    assert job.trigger.interval == timedelta(minutes=7)
    assert job.kwargs == {"container": container}


async def test_sheet_sync_history_is_purged_nightly(container) -> None:
    scheduler = create_scheduler(container, SyncSettings())

    job = scheduler.get_job("purge_sheet_syncs")

    assert job is not None
    assert isinstance(job.trigger, CronTrigger)
    assert str(job.trigger.fields[job.trigger.FIELD_NAMES.index("hour")]) == "4"


async def test_each_job_run_gets_its_own_request_scope(container) -> None:
    scheduler = create_scheduler(container, SyncSettings())
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


async def test_sheets_sync_job_runs_under_the_scheduler(container, db_session, sheets_client) -> None:
    await make_club(db_session, spreadsheet_id="s1", sheet_name="list")
    sheets_client.set_sheet("s1", "list", [])
    scheduler = create_scheduler(container, SyncSettings())
    finished: asyncio.Future[JobExecutionEvent] = asyncio.get_running_loop().create_future()
    scheduler.add_listener(finished.set_result, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    scheduler.start(paused=True)
    try:
        job = scheduler.get_job("sync_sheets")
        assert job is not None
        job.modify(next_run_time=datetime.now(UTC))
        scheduler.resume()
        event = await asyncio.wait_for(finished, timeout=5)
    finally:
        scheduler.shutdown(wait=False)

    assert event.job_id == "sync_sheets"
    assert event.exception is None
