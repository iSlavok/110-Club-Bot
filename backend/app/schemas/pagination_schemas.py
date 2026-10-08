from pydantic import BaseModel, Field

MAX_PER_PAGE = 200


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number, starting from 1")
    per_page: int = Field(default=50, ge=1, le=MAX_PER_PAGE, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


class Paginated[T](BaseModel):
    items: list[T]
    total: int
