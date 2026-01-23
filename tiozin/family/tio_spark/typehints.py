from typing import Literal, TypeAlias

from pyspark.sql import DataFrame, DataFrameWriter
from pyspark.sql.streaming.readwriter import DataStreamWriter

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

SparkPlan: TypeAlias = DataFrame | DataFrameWriter | DataStreamWriter | None
