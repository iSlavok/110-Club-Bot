from app import texts
from app.schemas import ClubAccess


def _access(invite_link: str | None) -> ClubAccess:
    return ClubAccess(club_title="Химия", block_title="6", invite_link=invite_link)


def test_access_without_a_join_link() -> None:
    assert texts.vk_link.access_status([_access(None)]) == "Ты в клубе Химия, блок 6."


def test_join_link_adds_the_hint_to_the_button() -> None:
    text = texts.vk_link.access_status([_access("https://t.me/+join1")])

    assert text == f"Ты в клубе Химия, блок 6.\n{texts.vk_link.JOIN_HINT}"
