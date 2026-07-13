from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, BeforeValidator

from tiozin.api.enums import Cadence
from tiozin.utils import as_utc

from .metadata.batch.watermark import check_watermark, parse_watermark

TechnicalTime = Annotated[
    AwareDatetime,
    AfterValidator(as_utc),
]

NominalTime = Annotated[
    TechnicalTime,
    AfterValidator(
        lambda dt: Cadence.MINUTELY.truncate(dt)
    ),  # NOTE: Hardcoded for now; minute truncation will become the default.
]

Watermark = Annotated[
    int | date | datetime,
    BeforeValidator(lambda value: parse_watermark(value)),
    AfterValidator(lambda value: check_watermark(value)),
]
