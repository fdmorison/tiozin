"""
tio_duckdb public API.

This module defines the public, stable interface of the DuckDB provider
used by Tiozin pipelines.

Only the symbols exported here are considered part of the supported API.
All other modules and classes inside this package are internal implementation
details and may change without notice.
"""

# Public base abstractions
from .bases import (
    DuckdbCoTransform,
    DuckdbInput,
    DuckdbOutput,
    DuckdbTransform,
)

# Inputs
from .inputs.file_input import DuckdbFileInput

# Outputs
from .outputs.file_output import DuckdbFileOutput
from .outputs.postgres_output import DuckdbPostgresOutput

# Runners
from .runners.duckdb_runner import DuckdbRunner

# Transforms
from .transforms.sql_transform import DuckdbSqlTransform
from .transforms.word_count_transform import DuckdbWordCountTransform

__all__ = [
    "DuckdbInput",
    "DuckdbTransform",
    "DuckdbCoTransform",
    "DuckdbOutput",
    "DuckdbRunner",
    "DuckdbFileInput",
    "DuckdbFileOutput",
    "DuckdbPostgresOutput",
    "DuckdbSqlTransform",
    "DuckdbWordCountTransform",
]
