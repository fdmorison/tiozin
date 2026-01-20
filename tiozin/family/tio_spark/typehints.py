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
