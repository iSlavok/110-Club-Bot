from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(description="Machine-readable error code, e.g. LESSON_NOT_FOUND")
    message: str = Field(description="Human-readable description")


class FieldError(BaseModel):
    loc: list[str | int] = Field(description="Path to the invalid value, e.g. ['body', 'title']")
    message: str = Field(description="What is wrong with the value")


class ValidationErrorResponse(ErrorResponse):
    fields: list[FieldError] = Field(description="Per-field validation errors")
