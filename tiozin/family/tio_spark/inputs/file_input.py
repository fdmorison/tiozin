from __future__ import annotations

from typing import TYPE_CHECKING

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import element_at, input_file_name, split

from tiozin.api import Input
from tiozin.exceptions import RequiredArgumentError

from ..typehints import SparkFileFormat

if TYPE_CHECKING:
    from tiozin.api import Context

INPUT_FILE_PATH_COLUMN = "input_file_path"
INPUT_FILE_NAME_COLUMN = "input_file_name"


class SparkFileInput(Input[DataFrame]):
    """
    Reads files into a Spark DataFrame using Spark.

    This input reads data from disk or external storage in any format supported
    by Spark, such as Parquet, CSV, JSON, etc. Read behavior and options follow
    standard Spark semantics.

    For advanced and format-specific options, refer to Spark documentation at:

    https://spark.apache.org/docs/latest/sql-data-sources-load-save-functions.html

    Attributes:
        path:
            Path to the file or directory to read from.

        format:
            File format used for reading the data.

        include_input_file:
            Whether to include input file metadata columns in the DataFrame.
            When enabled, adds ``input_file_path`` and ``input_file_name``.

        **options:
            Additional Spark reader options passed directly to Spark.

    Examples:

        ```python
        SparkFileInput(
            path="/data/events",
            format="json",
            include_input_file=True,
            inferSchema=True,
        )
        ```

        ```yaml
        inputs:
          - type: SparkFileInput
            path: /data/events
            format: json
            include_input_file: true
            inferSchema: true
        ```
    """

    def __init__(
        self,
        path: str,
        format: SparkFileFormat = None,
        include_input_file: bool = False,
        **options,
    ) -> None:
        super().__init__(**options)
        RequiredArgumentError.raise_if_missing(
            path=path,
        )
        self.path = path
        self.format = format or "parquet"
        self.include_input_file = include_input_file

    def read(self, context: Context) -> DataFrame:
        runner = context.job.runner
        spark: SparkSession = runner.session
        reader = spark.readStream if runner.streaming else spark.read

        self.info(f"Reading {self.format} from {self.path}")

        df = (
            reader.format(self.format)
            .options(**self.options)
            .load(
                self.path,
            )
        )

        if self.include_input_file:
            df = df.withColumn(
                INPUT_FILE_PATH_COLUMN,
                input_file_name(),
            ).withColumn(
                INPUT_FILE_NAME_COLUMN,
                element_at(split(INPUT_FILE_PATH_COLUMN, "/"), -1),
            )

        return df
