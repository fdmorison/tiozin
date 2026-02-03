from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col,
    input_file_name,
    lit,
    regexp_replace,
    split_part,
    when,
)

from tiozin.api import Context, conventions
from tiozin.exceptions import InvalidInputError, RequiredArgumentError
from tiozin.utils import as_list, trim_lower

from .. import SparkInput
from ..typehints import SparkFileFormat


class SparkFileInput(SparkInput):
    """
    Reads files into a Spark DataFrame using Spark.

    This input reads data from disk or external storage in any format supported by Spark, such as
    Parquet, CSV, JSON, ORC, Avro, text, XML, and binaryFile. Read behavior and options follow
    standard Spark semantics. When streaming is enabled, exactly one directory path is required.

    For advanced and format-specific options, refer to Spark documentation at:

    https://spark.apache.org/docs/latest/sql-data-sources-load-save-functions.html

    Attributes:
        path:
            Path (or list of paths) to the file or directory to read from.

        format:
            File format used for reading the data. Defaults to ``"parquet"``.

        explode_filepath:
            When enabled, expands the input file path into multiple semantic columns:
            ``filesize``, ``dirpath``, ``dirname``, ``filepath``, ``filename``, ``filestem``,
            and ``filetype``. While ``filesize`` is not derived directly from the file path, it
            is considered part of the minimal file structural context provided by this option.
            This option is intentionally scoped to file-level structure and does not include
            format-specific metadata (e.g. Parquet metadata).

        **options:
            Additional Spark reader options passed directly to Spark.

    Examples:

        ```python
        SparkFileInput(
            path="/data/events",
            format="json",
            explode_filepath=True,
            inferSchema=True,
        )
        ```

        ```yaml
        inputs:
          - type: SparkFileInput
            path: /data/events
            format: json
            explode_filepath: true
            inferSchema: true
        ```
    """

    def __init__(
        self,
        path: str | list[str] = None,
        format: SparkFileFormat = None,
        explode_filepath: bool = False,
        **options,
    ) -> None:
        super().__init__(**options)
        RequiredArgumentError.raise_if_missing(
            path=path,
        )
        self.path = as_list(path)
        self.format = trim_lower(format or "parquet")
        self.explode_filepath = explode_filepath

    def read(self, context: Context) -> DataFrame:
        self.info(f"Reading {self.format} from {self.path}")

        reader = self.spark.read
        paths = self.path
        is_streaming = context.runner.streaming

        if is_streaming:
            InvalidInputError.raise_if(
                len(self.path) != 1,
                "Spark streaming file sources require exactly one directory path "
                f"when streaming is enabled. Received: {self.path}",
            )
            paths = paths[0]
            reader = self.spark.readStream

        reader = reader.format(self.format).options(**self.options)
        df = reader.load(paths)

        if self.explode_filepath:
            filepath = input_file_name()
            filename = split_part(filepath, lit("/"), lit(-1))
            df = (
                df.withColumn(
                    conventions.FILESIZE_COLUMN,
                    col("_metadata.file_size"),
                )
                .withColumn(
                    conventions.DIRPATH_COLUMN,
                    regexp_replace(filepath, "/[^/]+$", ""),
                )
                .withColumn(
                    conventions.DIRNAME_COLUMN,
                    split_part(filepath, lit("/"), lit(-2)),
                )
                .withColumn(
                    conventions.FILEPATH_COLUMN,
                    filepath,
                )
                .withColumn(
                    conventions.FILENAME_COLUMN,
                    filename,
                )
                .withColumn(
                    conventions.FILESTEM_COLUMN,
                    when(
                        filename.contains("."),
                        split_part(filename, lit("."), lit(-2)),
                    ).otherwise(filename),
                )
                .withColumn(
                    conventions.FILETYPE_COLUMN,
                    when(
                        filename.contains("."),
                        split_part(filename, lit("."), lit(-1)),
                    ).otherwise(lit("")),
                )
            )

        return df
