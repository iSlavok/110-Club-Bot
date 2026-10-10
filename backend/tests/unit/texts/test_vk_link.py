from datetime import UTC, datetime, timedelta

from app import texts
from app.schemas import ClubAccess

STARTS_AT = datetime(2026, 10, 4, 21, 0, tzinfo=UTC)


def _access(*, is_upcoming: bool, invite_link: str | None) -> ClubAccess:
    return ClubAccess(
        club_title="Химия",
        block_title="Блок 6",
        block_starts_at=STARTS_AT,
        block_ends_at=STARTS_AT + timedelta(days=60),
        is_upcoming=is_upcoming,
        invite_link=invite_link,
    )


def test_upcoming_block_shows_its_moscow_start_day() -> None:
    text = texts.vk_link.access_status([_access(is_upcoming=True, invite_link=None)])

    assert text == "Ты в клубе Химия, блок Блок 6 — начнётся 05.10."


def test_join_link_adds_the_hint_to_the_button() -> None:
    text = texts.vk_link.access_status([_access(is_upcoming=False, invite_link="https://t.me/+join1")])

    assert text == f"Ты в клубе Химия, блок Блок 6.\n{texts.vk_link.JOIN_HINT}"
