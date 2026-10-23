from app import texts
from app.schemas import ClubAccess, VkCandidate


def _access(invite_link: str | None) -> ClubAccess:
    return ClubAccess(club_title="Химия", block_title="6", invite_link=invite_link)


def test_candidate_shows_name_and_page() -> None:
    candidate = VkCandidate(vk_id=42, full_name="Катя <Орлова>")

    assert texts.vk_link.confirm_candidate(candidate) == (
        "Это твоя страница?\n<b>Катя &lt;Орлова&gt;</b> — vk.com/id42\n\n"
        "После подтверждения привязку нельзя будет изменить."
    )
    assert texts.vk_link.confirm_button(candidate) == "Это я: Катя <Орлова>"


def test_candidate_without_a_name_shows_only_the_page() -> None:
    candidate = VkCandidate(vk_id=42, full_name="")

    assert texts.vk_link.confirm_candidate(candidate) == (
        "Это твоя страница?\nvk.com/id42\n\nПосле подтверждения привязку нельзя будет изменить."
    )
    assert texts.vk_link.confirm_button(candidate) == "Это я"


def test_access_without_a_join_link() -> None:
    assert texts.vk_link.access_status([_access(None)]) == "Ты в клубе Химия, блок 6."


def test_join_link_adds_the_hint_to_the_button() -> None:
    text = texts.vk_link.access_status([_access("https://t.me/+join1")])

    assert text == f"Ты в клубе Химия, блок 6.\n{texts.vk_link.JOIN_HINT}"
