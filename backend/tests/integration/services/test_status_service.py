from datetime import UTC, datetime

import pytest

from app.services import StatusService
from tests.factories import make_block, make_club, make_membership, make_user


@pytest.fixture
async def service(request_container) -> StatusService:
    return await request_container.get(StatusService)


async def test_reports_active_clubs_by_title(service, db_session) -> None:
    await make_club(db_session, title="Химия")
    await make_club(db_session, title="Биология")
    await make_club(db_session, title="Архив", is_active=False)

    report = await service.build()

    assert [status.club.title for status in report.clubs] == ["Биология", "Химия"]


async def test_reports_current_block_members(service, db_session) -> None:
    club = await make_club(db_session)
    block = await make_block(db_session, club, starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    membership = await make_membership(db_session, block)
    await make_membership(db_session, block)
    await make_user(db_session, vk_id=membership.vk_id)

    report = await service.build()

    [status] = report.clubs
    assert status.current_block is not None
    assert status.current_block.block.id == block.id
    assert (status.current_block.members, status.current_block.members_with_tg) == (2, 1)


async def test_club_without_current_block(service, db_session) -> None:
    await make_club(db_session)

    report = await service.build()

    [status] = report.clubs
    assert status.current_block is None


async def test_no_active_clubs(service) -> None:
    report = await service.build()

    assert report.clubs == []
