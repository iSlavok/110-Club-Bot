import re
from datetime import datetime
from types import MappingProxyType

from sqlalchemy import BigInteger, DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Server-generated values come back via RETURNING; otherwise reading them after commit is a lazy load (async error).
    __mapper_args__ = MappingProxyType({"eager_defaults": True})

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, sort_order=-1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), sort_order=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        sort_order=1,
    )

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return _CAMEL_BOUNDARY.sub("_", cls.__name__).lower() + "s"
