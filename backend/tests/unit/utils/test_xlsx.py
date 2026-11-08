from app.utils import build_xlsx
from tests.xlsx import read_xlsx


def test_writes_headers_and_rows() -> None:
    content = build_xlsx(("VK", "Имя"), [["https://vk.com/id1", "Аня"], [None, "Борис"]])

    assert read_xlsx(content) == [["VK", "Имя"], ["https://vk.com/id1", "Аня"], [None, "Борис"]]


def test_empty_export_keeps_headers() -> None:
    assert read_xlsx(build_xlsx(("VK",), [])) == [["VK"]]
