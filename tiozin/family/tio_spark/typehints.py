from typing import TYPE_CHECKING, Literal, TypeAlias

from pyspark.sql import DataFrame, DataFrameWriter
from pyspark.sql.connect.dataframe import DataFrame as ConnectDataFrame
from pyspark.sql.connect.readwriter import DataFrameWriter as ConnectDataFrameWriter
from pyspark.sql.connect.streaming.readwriter import DataStreamWriter as ConnectDataStreamWriter
from pyspark.sql.streaming.readwriter import DataStreamWriter

from .bases import SparkCoTransform, SparkInput, SparkOutput, SparkTransform

if TYPE_CHECKING:
    from .writers.table_writer import TioSparkTableWriter

SparkEtlStep: TypeAlias = SparkInput | SparkTransform | SparkCoTransform | SparkOutput

SparkFileFormat = Literal[
    # Core / common
    "parquet",
    "csv",
    "json",
    "orc",
    "avro",
    "text",
    # Semi-structured / external libs
    "xml",
    "binaryFile",
    # Hadoop / legacy
    "sequenceFile",
]

SparkWriteMode = Literal[
    "append",
    "overwrite",
    "error",
    "errorifexists",
    "ignore",
]

TioSparkTableOutputMode = Literal[
    "append",
    "overwrite",
    "truncate",
    "overwrite_partitions",
    "merge",
]

SparkIcebergCatalogType = Literal[
    "hive",
    "hadoop",
    "rest",
    "glue",
    "jdbc",
    "nessie",
]

SparkIcebergClass = Literal[
    "org.apache.iceberg.spark.SparkCatalog",
    "org.apache.iceberg.spark.SparkSessionCatalog",
]

SparkPlan: TypeAlias = (
    "DataFrame"
    " | DataFrameWriter"
    " | TioSparkTableWriter"
    " | DataStreamWriter"
    " | ConnectDataFrame"
    " | ConnectDataFrameWriter"
    " | ConnectDataStreamWriter"
    " | None"
)
