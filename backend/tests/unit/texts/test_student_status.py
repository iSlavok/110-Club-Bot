from app import texts
from app.schemas import ClubAccess, StudentClubStatus, StudentStatus


def _club(
    *,
    title: str = "Химия",
    in_chat: bool | None = True,
    invite_link: str | None = None,
    next_block_title: str | None = None,
) -> StudentClubStatus:
    access = ClubAccess(club_title=title, block_title="6", invite_link=invite_link)
    return StudentClubStatus(access=access, in_chat=in_chat, next_block_title=next_block_title)


def test_unlinked_user_is_sent_to_vk() -> None:
    assert texts.student_status.student_status(StudentStatus(vk_id=None, clubs=[])) == texts.student_status.NOT_LINKED


def test_admin_without_vk_sees_the_clubs() -> None:
    text = texts.student_status.student_status(StudentStatus(vk_id=None, clubs=[_club()]))

    assert text == "<b>Клуб Химия, блок 6</b>\nТы в чате клуба."


def test_linked_user_without_access() -> None:
    text = texts.student_status.student_status(StudentStatus(vk_id=4242, clubs=[]))

    assert text == f"ВК: vk.com/id4242\n\n{texts.student_status.NO_ACCESS}"


def test_clubs_with_next_block_and_chat() -> None:
    status = StudentStatus(
        vk_id=4242,
        clubs=[
            _club(title="Химия & <био>", next_block_title="7"),
            _club(title="Физика", in_chat=False, invite_link="https://t.me/+join1"),
        ],
    )

    assert texts.student_status.student_status(status) == (
        "ВК: vk.com/id4242\n\n"
        "<b>Клуб Химия &amp; &lt;био&gt;, блок 6</b>\n"
        "В следующем блоке 7 ты тоже есть.\nТы в чате клуба.\n\n"
        "<b>Клуб Физика, блок 6</b>\nВступи в чат по кнопке ниже."
    )


def test_chat_lines() -> None:
    no_chat = texts.student_status.student_status(StudentStatus(vk_id=1, clubs=[_club(in_chat=None)]))
    no_link = texts.student_status.student_status(StudentStatus(vk_id=1, clubs=[_club(in_chat=False)]))

    assert "чат" not in no_chat
    assert no_link.endswith("Ссылку на чат сейчас получить не удалось. Напиши куратору.")
