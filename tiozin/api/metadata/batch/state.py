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

        watermarks:
            Business marks. Named watermarks tracking how far the data has
            progressed. Values are an int, date, datetime, or `None`,
            serialized as canonical strings and read back as their original
            type. The framework never initializes them; plugins decide how
            each one starts.
    """

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        validate_default=True,
    )

    start: NominalTime | None = Field(default_factory=epoch)
    end: NominalTime | None = Field(default_factory=utcnow)
    watermarks: dict[str, Watermark | None] = Field(default_factory=dict)

    @field_validator("start", "end")
    @classmethod
    def _normalize_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.astimezone(UTC)

    @field_serializer("watermarks")
    def _serialize_watermarks(
        self, value: dict[str, Watermark | None]
    ) -> dict[str, RawWatermark | None]:
        return {name: serialize_watermark(mark) for name, mark in value.items()}

    def advance_to(self, end: datetime | None) -> BatchState:
        """
        Resolves the next processing state.

        Args:
            end: New end of the execution window, or `None` to leave the state unchanged.

        Returns:
            A new state with the execution window advanced and the watermarks
            preserved, or `self` if `end` is `None`.
        """
        if not end:
            return self

        return BatchState(start=self.end, end=end, watermarks=self.watermarks)
