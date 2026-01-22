from typing import Literal

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
