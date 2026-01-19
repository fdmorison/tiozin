from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pyspark.sql import DataFrame, DataFrameWriter

from tiozin.api import Output

if TYPE_CHECKING:
    from tiozin.api import StepContext

SparkFormat = Literal["parquet", "csv", "json", "orc", "avro", "delta", "iceberg", "jdbc"]
SparkMode = Literal["append", "overwrite", "error", "errorifexists", "ignore"]


class SparkFileOutput(Output[DataFrame]):
    """
    Spark Output for writing DataFrames to various destinations.

    Supports common formats like parquet, csv, json, orc, avro,
    delta, iceberg, and jdbc.

    Returns a DataFrameWriter for lazy execution by the SparkRunner.
    """

    def __init__(
        self,
        path: str = None,
        format: SparkFormat = "parquet",
        mode: SparkMode = "overwrite",
        partition_by: list[str] = None,
        **options,
    ) -> None:
        super().__init__(**options)
        self.path = path
        self.format = format
        self.mode = mode
        self.partition_by = partition_by or []

    def write(self, context: StepContext, data: DataFrame) -> DataFrameWriter:
        writer = data.write.format(self.format).mode(self.mode)

        if self.partition_by:
            writer = writer.partitionBy(*self.partition_by)

        for key, value in self.options.items():
            writer = writer.option(key, value)

        if self.path:
            writer = writer.option("path", self.path)

        self.info(f"Prepared {self.format} write to: {self.path or 'default location'}")
        return writer
