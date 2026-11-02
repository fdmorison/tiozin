from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

TAGS = {"dataset", "mode", "format"}
COUNTS = {"rows_written", "bytes_written"}
GAUGES = {"rows_total", "bytes_total"}


class OutputMetrics(BaseModel):
    """
    Normalized metrics of a write, shared by every plugin that reports them.

    A metric is None when it is unknown, which is different from zero. Metric values
    given as numeric strings are converted to integers.
    """

    dataset: str = Field(description="Name of the dataset written.")
    mode: str | None = Field(None, description="Write mode used.")
    format: str | None = Field(None, description="Format of the data written.")
    rows_written: int | None = Field(None, description="Rows written by the write.")
    rows_total: int | None = Field(None, description="Rows in the dataset after the write.")
    bytes_written: int | None = Field(None, description="Bytes written by the write.")
    bytes_total: int | None = Field(None, description="Size of the dataset after the write.")

    def to_dict(self) -> dict[str, Any]:
        """
        Returns every field, including unknown metrics.
        """
        return self.model_dump()

    def tags(self) -> dict[str, str]:
        """
        Returns the fields that identify the write.
        """
        return self.model_dump(include=TAGS, exclude_none=True)

    def counts(self) -> dict[str, int]:
        """
        Returns the known metrics that measure a single write.
        """
        return self.model_dump(include=COUNTS, exclude_none=True)

    def gauges(self) -> dict[str, int]:
        """
        Returns the known metrics that measure the dataset after the write.
        """
        return self.model_dump(include=GAUGES, exclude_none=True)
