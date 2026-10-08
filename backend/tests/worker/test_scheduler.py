from apscheduler.triggers.cron import CronTrigger

from worker import create_scheduler


async def test_auth_cleanup_runs_nightly(container) -> None:
    scheduler = create_scheduler(container)

    job = scheduler.get_job("purge_expired_auth")

    assert job is not None
    assert isinstance(job.trigger, CronTrigger)
    assert str(job.trigger.fields[job.trigger.FIELD_NAMES.index("hour")]) == "4"
