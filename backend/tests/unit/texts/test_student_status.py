from datetime import UTC, datetime

from app import texts
from app.schemas import ClubAccess, StudentClubStatus, StudentStatus

# 05.10 and 04.12 in Moscow.
STARTS_AT = datetime(2026, 10, 4, 21, 0, tzinfo=UTC)
ENDS_AT = datetime(2026, 12, 3, 21, 0, tzinfo=UTC)


def _club(
    *,
    title: str = "Химия",
    is_upcoming: bool = False,
    in_chat: bool | None = True,
    invite_link: str | None = None,
    next_block_title: str | None = None,
) -> StudentClubStatus:
    access = ClubAccess(
        club_title=title,
        block_title="Блок 6",
        block_starts_at=STARTS_AT,
        block_ends_at=ENDS_AT,
        is_upcoming=is_upcoming,
        invite_link=invite_link,
    )
    return StudentClubStatus(access=access, in_chat=in_chat, next_block_title=next_block_title)


def test_unlinked_user_is_sent_to_vk() -> None:
    assert texts.student_status.student_status(StudentStatus(vk_id=None, clubs=[])) == texts.student_status.NOT_LINKED


def test_linked_user_without_access() -> None:
    text = texts.student_status.student_status(StudentStatus(vk_id=4242, clubs=[]))

    assert text == f"VK: vk.com/id4242\n\n{texts.student_status.NO_ACCESS}"


def test_clubs_with_block_next_block_and_chat() -> None:
    status = StudentStatus(
        vk_id=4242,
        clubs=[
            _club(title="Химия & <био>", next_block_title="Блок 7"),
            _club(title="Физика", is_upcoming=True, in_chat=False, invite_link="https://t.me/+join1"),
        ],
    )

    assert texts.student_status.student_status(status) == (
        "VK: vk.com/id4242\n\n"
        "<b>Химия &amp; &lt;био&gt;</b>\nБлок: Блок 6 (05.10–04.12)\n"
        "В следующем блоке (Блок 7) ты тоже есть.\nЧат: ты в чате.\n\n"
        "<b>Физика</b>\nБлок: Блок 6 (05.10–04.12), ещё не начался\n"
        "Чат: ты ещё не в чате — вступай по кнопке ниже, бот одобрит заявку сам."
    )


def test_chat_lines() -> None:
    no_chat = texts.student_status.student_status(StudentStatus(vk_id=1, clubs=[_club(in_chat=None)]))
    no_link = texts.student_status.student_status(StudentStatus(vk_id=1, clubs=[_club(in_chat=False)]))

    assert "Чат" not in no_chat
    assert no_link.endswith("Чат: ты ещё не в чате, а ссылку бот сейчас получить не смог. Напиши куратору.")
