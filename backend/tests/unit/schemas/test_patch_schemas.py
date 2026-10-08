import pytest
from pydantic import ValidationError

from app.schemas import Maybe, PatchSchema


class NotePatch(PatchSchema):
    title: Maybe[str]
    note: Maybe[str | None]


def test_omitted_fields_are_unset() -> None:
    patch = NotePatch.model_validate({})

    assert not patch.title.is_set
    assert patch.is_empty()


def test_explicit_null_is_set() -> None:
    patch = NotePatch.model_validate({"note": None})

    assert patch.note.is_set
    assert patch.note.value is None
    assert not patch.is_empty()


def test_apply_keeps_current_value_when_unset() -> None:
    patch = NotePatch.model_validate({"title": "new"})

    assert patch.title.apply("old") == "new"
    assert patch.note.apply("kept") == "kept"


def test_inner_type_is_validated() -> None:
    with pytest.raises(ValidationError):
        NotePatch.model_validate({"title": None})


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        NotePatch.model_validate({"color": "red"})


def test_json_schema_marks_fields_optional() -> None:
    schema = NotePatch.model_json_schema()

    assert "required" not in schema
