from __future__ import annotations

from datetime import UTC, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)

from tiozin.utils.helpers import epoch, utcnow

from ...types import NominalTime, Watermark
from .watermark import RawWatermark, serialize_watermark


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
        validate_default=True,
    )

    start: NominalTime | None = Field(default_factory=epoch)
    end: NominalTime | None = Field(default_factory=utcnow)
    watermark: Watermark | None = Field(default_factory=epoch)

    @field_validator("start", "end")
    @classmethod
    def _normalize_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.astimezone(UTC)

    @field_serializer("watermark")
    def _serialize_watermark(self, value: Watermark) -> RawWatermark:
        return serialize_watermark(value)

    def advance_to(self, end: datetime | None) -> BatchState:
        """
        Resolves the next processing state.

        Args:
            end: New end of the execution window, or `None` to leave the state unchanged.

        Returns:
            A new state with the execution window advanced and the watermark
            preserved, or `self` if `end` is `None`.
        """
        if not end:
            return self

        return BatchState(start=self.end, end=end, watermark=self.watermark)
