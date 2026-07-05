from __future__ import annotations

from datetime import UTC, datetime

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
)

from .watermark import RawWatermark, Watermark, serialize_watermark


class BatchState(BaseModel):
    """
    Typed processing state of a batch, replicated across executions.

    Unlike `attributes`, which holds arbitrary job-specific metadata, `state`
    is a predefined, evolvable structure that the framework declares and
    transports but does not manage. Its semantics belong to the job.

    Attributes:
        start:
            Technical mark. UTC datetime where the execution window begins.

        end:
            Technical mark. UTC datetime where the execution window ends.

        watermark:
            Business mark. How far the data itself has progressed. Accepts an
            int, date, or datetime, both on construction and on assignment,
            and is read back as the same type. Serialized as a canonical,
            lexicographically ordered string so that watermarks of the same
            type compare correctly at rest. Canonical strings are parsed back
            into their original type on construction.
    """

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
    )

    start: AwareDatetime | None = None
    end: AwareDatetime | None = None
    watermark: Watermark | None = None

    @field_validator("start", "end")
    @classmethod
    def _normalize_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.astimezone(UTC)

    @field_serializer("watermark")
    def _serialize_watermark(self, value: Watermark) -> RawWatermark:
        return serialize_watermark(value)
