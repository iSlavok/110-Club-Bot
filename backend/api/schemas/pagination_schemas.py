import math
from collections.abc import Callable
from typing import Self

from pydantic import BaseModel, Field, computed_field

from app.schemas import PageParams, Paginated


class Page[T](BaseModel):
    items: list[T] = Field(description="Items of the current page")
    page: int = Field(description="Current page number, starting from 1")
    per_page: int = Field(description="Requested page size")
    total_items: int = Field(description="Total number of items matching the query")

    @computed_field(description="Total number of pages")
    @property
    def total_pages(self) -> int:
        return math.ceil(self.total_items / self.per_page)

    @classmethod
    def from_paginated[S](cls, paginated: Paginated[S], params: PageParams, convert: Callable[[S], T]) -> Self:
        items = [convert(item) for item in paginated.items]
        return cls(items=items, page=params.page, per_page=params.per_page, total_items=paginated.total)
