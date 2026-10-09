import pytest

from app.utils import VkIdReference, VkScreenNameReference, parse_vk_reference


@pytest.mark.parametrize(
    "text",
    [
        "vk.com/id123",
        "https://vk.com/id123",
        "http://m.vk.com/id123/",
        "https://vk.ru/id123?w=wall123_1",
        "  www.vk.com/ID123  ",
        "id123",
        "123",
        "@id123",
    ],
)
def test_numeric_ids(text: str) -> None:
    assert parse_vk_reference(text) == VkIdReference(123)


@pytest.mark.parametrize(
    "text",
    [
        "https://vk.com/kate.orlova",
        "vk.com/Kate.Orlova#profile",
        "m.vk.com/kate.orlova",
        "@kate.orlova",
        "kate.orlova",
    ],
)
def test_screen_names(text: str) -> None:
    assert parse_vk_reference(text) == VkScreenNameReference("kate.orlova")


@pytest.mark.parametrize(
    "text",
    [
        "",
        "@",
        "Привет, это я",
        "https://example.com/kate.orlova",
        "https://vk.com/",
        "https://vk.com/wall/123",
        "ftp://vk.com/id123",
        "id0",
        "0",
        "99999999999999999999",
        "kate orlova",
    ],
)
def test_rejects_non_profile_text(text: str) -> None:
    assert parse_vk_reference(text) is None
