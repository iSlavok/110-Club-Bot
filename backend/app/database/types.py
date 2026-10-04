from enum import StrEnum

from sqlalchemy import Enum


# Stored as plain strings: native PG enums need ALTER TYPE and are invisible to alembic autogenerate.
def str_enum[E: StrEnum](enum_cls: type[E], length: int = 32) -> Enum:
    return Enum(
        enum_cls,
        native_enum=False,
        length=length,
        values_callable=lambda members: [member.value for member in members],
    )
