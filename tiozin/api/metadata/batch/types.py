from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, BeforeValidator

from tiozin.api.enums import Cadence

from .watermark import check_watermark, parse_watermark

NominalTime = Annotated[
    AwareDatetime,
    AfterValidator(Cadence.MINUTE.truncate),
]

Watermark = Annotated[
    int | date | AwareDatetime,
    BeforeValidator(lambda value: parse_watermark(value)),
    AfterValidator(lambda value: check_watermark(value)),
]
