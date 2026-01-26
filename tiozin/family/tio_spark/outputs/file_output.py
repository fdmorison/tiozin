from __future__ import annotations

from typing import TYPE_CHECKING

from pyspark.sql import DataFrame, DataFrameWriter

from tiozin.api import Output
from tiozin.exceptions import RequiredArgumentError
from tiozin.utils.helpers import as_list

from ..typehints import SparkFileFormat, SparkWriteMode

if TYPE_CHECKING:
    from tiozin.api import Context


class SparkFileOutput(Output[DataFrame]):
    """
    Writes a Spark DataFrame to files using Spark.

    This output writes DataFrames to disk or external storage in any format
    supported by Spark, such as Parquet, CSV, JSON, etc. Write behavior and
    options follow standard Spark semantics.

    For advanced and format-specific options, refer to Spark documentation at:

    https://spark.apache.org/docs/latest/sql-data-sources-load-save-functions.html

    Attributes:
        path:
            Target path where output files will be written.

        format:
            File format used for writing the data.

        mode:
            Write mode used by Spark.

        partition_by:
            Column name or list of column names used to partition the output
            files.

        **options:
            Additional Spark writer options passed directly to Spark.

    Examples:

        ```python
        SparkFileOutput(
            path="/data/events",
            format="json",
            mode="overwrite",
            partition_by=["date"],
            compression="gzip",
        )
        ```

        ```yaml
        outputs:
          - type: SparkFileOutput
            path: /data/events
            format: json
            mode: overwrite
            partition_by: ["date"]
            compression: gzip
        ```
    """

    def __init__(
        self,
        path: str,
        format: SparkFileFormat = None,
        mode: SparkWriteMode = None,
        partition_by: list[str] = None,
        **options,
    ) -> None:
        super().__init__(**options)
        RequiredArgumentError.raise_if_missing(
            path=path,
        )

        self.path = path
        self.format = format or "parquet"
        self.mode = mode or "overwrite"
        self.partition_by = as_list(partition_by)

    def write(self, context: Context, data: DataFrame) -> DataFrameWriter:
        self.info(f"Writing {self.format} to {self.path}")

        writer = data.write.format(self.format).mode(self.mode)

        if self.partition_by:
            writer = writer.partitionBy(*self.partition_by)

        for key, value in self.options.items():
            writer = writer.option(key, value)

        writer = writer.option("path", self.path)

        return writer
