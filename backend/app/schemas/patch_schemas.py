from typing import Any, ClassVar, get_args, get_origin, overload

from pydantic import BaseModel, ConfigDict
from pydantic_core import core_schema


# Tells "field omitted" from "field sent as null" in PATCH bodies: omitted fields stay UNSET.
class Maybe[T]:
    UNSET: ClassVar["Maybe[Any]"]

    __slots__ = ("_is_set", "_value")

    def __init__(self, *value: T) -> None:
        self._is_set = bool(value)
        self._value = value[0] if value else None

    @property
    def is_set(self) -> bool:
        return self._is_set

    @property
    def value(self) -> T | None:
        return self._value

    @overload
    def apply(self, current: T) -> T: ...
    @overload
    def apply(self, current: T | None) -> T | None: ...
    def apply(self, current: T | None) -> T | None:
        return self._value if self._is_set else current

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:  # noqa: ANN401 - pydantic hook contract
        args = get_args(source_type)
        inner_schema = handler(args[0] if args else Any)
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(cls),
                core_schema.no_info_after_validator_function(cls, inner_schema),
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(lambda v: v.value),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: Any, handler: Any) -> dict[str, Any]:  # noqa: ANN401 - pydantic hook contract
        # An inline copy, not the $ref: pydantic resolves a returned $ref to the shared definition and then writes
        # field keywords into it, which splits an enum into "-Input" and "-Output" variants.
        json_schema = dict(handler.resolve_ref_schema(handler(schema)))
        json_schema.pop("default", None)
        return json_schema

    def __repr__(self) -> str:
        return f"Maybe({self._value!r})" if self._is_set else "UNSET"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Maybe):
            return NotImplemented
        return (self._is_set, self._value) == (other._is_set, other._value)

    def __hash__(self) -> int:
        return hash((self._is_set, self._value))


Maybe.UNSET = Maybe()


class PatchSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    # Maybe fields are declared without a default; UNSET is injected so they become optional in the schema.
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:  # noqa: ANN401 - pydantic hook contract
        super().__pydantic_init_subclass__(**kwargs)
        patched = False
        for name, field_info in cls.model_fields.items():
            if field_info.is_required() and get_origin(cls.__annotations__.get(name)) is Maybe:
                field_info.default = Maybe.UNSET
                patched = True
        if patched:
            cls.model_rebuild(force=True)

    def is_empty(self) -> bool:
        return not any(getattr(self, name).is_set for name in type(self).model_fields)
