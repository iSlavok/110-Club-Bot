from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageResult[ModelType]:
    items: list[ModelType]
    total: int
