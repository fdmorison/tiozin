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
from .transforms.sql_transform import SparkSqlTransform
from .transforms.word_count_transform import SparkWordCountTransform

__all__ = [
    "SparkInput",
    "SparkTransform",
    "SparkCoTransform",
    "SparkOutput",
    "SparkRunner",
    "SparkIcebergRunner",
    "SparkFileInput",
    "SparkFileOutput",
    "SparkSqlTransform",
    "SparkWordCountTransform",
]
