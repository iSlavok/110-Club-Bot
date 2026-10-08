from api.schemas import Page
from app.schemas import PageParams, Paginated


def test_page_converts_items_and_counts_pages() -> None:
    paginated = Paginated[int](items=[1, 2], total=7)

    page = Page[str].from_paginated(paginated, PageParams(page=3, per_page=2), str)

    assert page.model_dump() == {"items": ["1", "2"], "page": 3, "per_page": 2, "total_items": 7, "total_pages": 4}


def test_offset_follows_page_number() -> None:
    assert PageParams(page=1, per_page=50).offset == 0
    assert PageParams(page=3, per_page=20).offset == 40
