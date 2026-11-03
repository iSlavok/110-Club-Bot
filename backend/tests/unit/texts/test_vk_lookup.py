from datetime import UTC, datetime

from app import texts
from app.schemas import UserDTO

NOW = datetime(2026, 9, 1, tzinfo=UTC)


def _user(vk_id: int | None) -> UserDTO:
    return UserDTO(
        id=1,
        tg_id=10,
        tg_username=None,
        full_name="Аня",
        vk_id=vk_id,
        vk_linked_at=None,
        created_at=NOW,
        updated_at=NOW,
    )


def test_linked_vk_is_a_link_and_a_copyable_address() -> None:
    assert texts.vk_lookup.student_vk(10, "Аня <А>", _user(5005)) == (
        'VK ученика <a href="tg://user?id=10">Аня &lt;А&gt;</a>:\n'
        '<a href="https://vk.com/id5005">Открыть страницу</a>\n'
        "Скопировать ссылку: <code>https://vk.com/id5005</code>"
    )


def test_student_without_vk() -> None:
    mention = '<a href="tg://user?id=10">Аня</a>'

    assert texts.vk_lookup.student_vk(10, "Аня", _user(None)) == f"{mention} не привязал VK."
    assert texts.vk_lookup.student_vk(10, "Аня", None) == f"{mention} ещё не писал боту, его VK неизвестен."
