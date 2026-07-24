from __future__ import annotations

from typing import Annotated, Any

from pydantic import AfterValidator, AwareDatetime, BeforeValidator, Field

from tiozin.utils import as_utc, check_time_ordered_id, generate_time_ordered_id, slugify

from .enums import Cadence

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

# An open mapping of arbitrary key-value metadata that propagates accross layers
Attributes = Annotated[
    dict[str, Any],
    Field(default=None),
    BeforeValidator(lambda value: dict(value) if value else {}),
]

# An open mapping of arbitrary key-value metadata that propagates accross executions
Bookmarks = Annotated[
    dict[str, Any],
    Field(default=None),
    BeforeValidator(lambda value: dict(value) if value else {}),
]

# A string normalized into a safe SQL and filesystem identifier.
Slug = Annotated[
    str,
    AfterValidator(slugify),
]
