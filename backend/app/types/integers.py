from typing import Annotated

from pydantic import Field

INT32_MAX = 2**31 - 1
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1

# Mirror the column types: a value Postgres cannot store must fail validation (422), not the query (500).
type BigInt = Annotated[int, Field(ge=INT64_MIN, le=INT64_MAX)]
type PositiveBigInt = Annotated[int, Field(ge=1, le=INT64_MAX)]
type PositiveInt32 = Annotated[int, Field(ge=1, le=INT32_MAX)]
