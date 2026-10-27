"""
tio_spark public API.

This module defines the public, stable interface of the Spark provider
used by Tiozin pipelines.

Only the symbols exported here are considered part of the supported API.
All other modules and classes inside this package are internal implementation
details and may change without notice.
"""

# Public base abstractions
from .bases import (
    SparkCoTransform,
    SparkInput,
    SparkOutput,
    SparkTransform,
)

# Inputs
from .inputs.file_input import SparkFileInput

# Outputs
from .outputs.file_output import SparkFileOutput
from .runners.spark_iceberg_runner import SparkIcebergRunner

# Runners
from .runners.spark_runner import SparkRunner

# Transforms
from .transforms.schema_inference_transform import SparkSchemaInferenceTransform
from .transforms.sql_transform import SparkSqlTransform
from .transforms.word_count_transform import SparkWordCountTransform

# Writers
from .writers.table_writer import TioSparkTableWriter

__all__ = [
    # Public base abstractions
    "SparkInput",
    "SparkTransform",
    "SparkCoTransform",
    "SparkOutput",
    # Runners
    "SparkRunner",
    "SparkIcebergRunner",
    # Inputs
    "SparkFileInput",
    # Outputs
    "SparkFileOutput",
    # Transforms
    "SparkSchemaInferenceTransform",
    "SparkSqlTransform",
    "SparkWordCountTransform",
    # Writers
    "TioSparkTableWriter",
]
