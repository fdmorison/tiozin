from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import element_at, input_file_name, split

from tiozin.api import Input

if TYPE_CHECKING:
    from tiozin.api import StepContext

SparkFormat = Literal["parquet", "csv", "json", "orc", "avro", "delta", "iceberg", "jdbc"]

INPUT_FILE_PATH_COLUMN = "input_file_path"
INPUT_FILE_NAME_COLUMN = "input_file_name"


class SparkFileInput(Input[DataFrame]):
    """
    Spark Input for reading data from various sources.

    Supports common formats like parquet, csv, json, orc, avro,
    delta, iceberg, and jdbc.

    The SparkSession must be active before execution. You can either:
    - Create a SparkSession manually before running the job
    - Use SparkRunner which manages the session lifecycle

    Attributes:
        path: Path to the file or directory to read.
        format: File format (parquet, csv, json, etc.).
        include_input_file: If True, adds '_source_file_path' and 'input_file_name' columns.
    """

    def __init__(
        self,
        path: str = None,
        format: SparkFormat = "parquet",
        include_input_file: bool = False,
        **options,
    ) -> None:
        super().__init__(**options)
        self.path = path
        self.format = format
        self.include_input_file = include_input_file

    def read(self, context: StepContext) -> DataFrame:
        spark = SparkSession.getActiveSession()
        reader = spark.read.format(self.format)
        reader = reader.options(**self.options)

        if self.path:
            df = reader.load(self.path)
        else:
            df = reader.load()

        if self.include_input_file:
            df = df.withColumn(
                INPUT_FILE_PATH_COLUMN,
                input_file_name(),
            ).withColumn(
                INPUT_FILE_NAME_COLUMN,
                element_at(split(INPUT_FILE_PATH_COLUMN, "/"), -1),
            )

        self.info(f"Read {self.format} from: {self.path or 'default location'}")
        return df
