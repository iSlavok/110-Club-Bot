from datetime import UTC, datetime

import pytest

from app.enums import LessonKind
from app.exceptions import UserNotRegisteredError
from app.schemas import ScheduleItem
from app.services import ScheduleService
from tests.factories import make_block, make_club, make_lesson, make_membership, make_user
from tests.providers import DEFAULT_NOW

TG_ID = 42
VK_ID = 4242
BLOCK_STARTS_AT = datetime(2026, 9, 1, tzinfo=UTC)
BLOCK_ENDS_AT = datetime(2026, 10, 31, tzinfo=UTC)


@pytest.fixture
async def service(request_container) -> ScheduleService:
    return await request_container.get(ScheduleService)


async def test_unregistered_user_is_sent_to_start(service) -> None:
    with pytest.raises(UserNotRegisteredError):
        await service.build(TG_ID)


async def test_unlinked_user_or_one_without_access_sees_nothing(service, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID)
    await make_user(db_session, tg_id=TG_ID + 1, vk_id=VK_ID)
    await make_block(db_session, await make_club(db_session))

    assert await service.build(TG_ID) == []
    assert await service.build(TG_ID + 1) == []


async def test_schedule_runs_to_the_end_of_the_access_block(service, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID, vk_id=VK_ID)
    club = await make_club(db_session, title="Химия")
    block = await make_block(db_session, club, title="Блок 5", starts_at=BLOCK_STARTS_AT, ends_at=BLOCK_ENDS_AT)
    await make_membership(db_session, block, vk_id=VK_ID)
    call_at = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)
    deadline = datetime(2026, 10, 2, 20, 59, tzinfo=UTC)
    await make_lesson(
        db_session,
        club,
        kind=LessonKind.CURATOR_CALL,
        title="Разбор",
        starts_at=call_at,
        homework_deadline_at=datetime(2026, 11, 2, tzinfo=UTC),
    )
    await make_lesson(
        db_session,
        club,
        title="Кислоты",
        starts_at=DEFAULT_NOW.replace(day=1, hour=8),
        homework_deadline_at=deadline,
    )
    await make_lesson(db_session, club, title="После блока", starts_at=BLOCK_ENDS_AT)

    [schedule] = await service.build(TG_ID)

    assert (schedule.club_title, schedule.block_title) == ("Химия", "Блок 5")
    assert schedule.items == [
        ScheduleItem(moment=deadline, lesson_kind=LessonKind.LESSON, lesson_title="Кислоты", is_homework_deadline=True),
        ScheduleItem(
            moment=call_at,
            lesson_kind=LessonKind.CURATOR_CALL,
            lesson_title="Разбор",
            is_homework_deadline=False,
        ),
    ]
