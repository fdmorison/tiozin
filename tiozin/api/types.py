from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any

from pydantic import AfterValidator, AwareDatetime, BeforeValidator, Field

from tiozin.utils import as_utc, check_time_ordered_id, generate_time_ordered_id

from .enums import Cadence
from .metadata.batch.watermark import check_watermark, parse_watermark

# Generates a time-ordered ID when the value is missing or None.
TimeOrderedId = Annotated[
    str,
    Field(default=None),
    BeforeValidator(lambda value: generate_time_ordered_id() if value is None else str(value)),
    AfterValidator(check_time_ordered_id),
]

# An aware datetime normalized to UTC.
TechnicalTime = Annotated[
    AwareDatetime,
    AfterValidator(as_utc),
]

# A technical time truncated to the current cadence.
NominalTime = Annotated[
    TechnicalTime,
    AfterValidator(lambda dt: Cadence.current().truncate(dt)),
]

# A non-negative integer counter defaulting to zero.
Counter = Annotated[
    int,
    Field(default=0, ge=0),
]

# An open mapping of arbitrary key-value metadata.
Attributes = Annotated[
    dict[str, Any],
    Field(default=None),
    BeforeValidator(lambda value: dict(value) if value else {}),
]

# A validated batch watermark represented as an integer, date, or datetime.
Watermark = Annotated[
    int | date | datetime,
    BeforeValidator(lambda value: parse_watermark(value)),
    AfterValidator(lambda value: check_watermark(value)),
]
