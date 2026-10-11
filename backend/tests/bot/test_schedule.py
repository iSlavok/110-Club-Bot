from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from app.services import ScheduleService
from bot.handlers.schedule import schedule
from tests.factories import make_block, make_club, make_lesson, make_membership, make_user

TG_ID = 42
VK_ID = 4242


async def test_schedule_replies_with_the_lessons_of_the_block(request_container, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID, vk_id=VK_ID)
    club = await make_club(db_session, title="Химия")
    await make_membership(db_session, await make_block(db_session, club, title="5"), vk_id=VK_ID)
    await make_lesson(db_session, club, title="Кислоты", starts_at=datetime(2026, 10, 2, 16, 0, tzinfo=UTC))
    message = AsyncMock()
    message.from_user = MagicMock(id=TG_ID)

    await schedule(message, await request_container.get(ScheduleService))

    message.answer.assert_awaited_once_with(
        "<b>Клуб Химия, блок 5</b>\n\nПт, 2 октября\n• 19:00 — урок «Кислоты»",
    )
