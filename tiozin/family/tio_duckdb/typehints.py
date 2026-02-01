from typing import Literal, TypeAlias

from duckdb import DuckDBPyRelation

from .bases import DuckdbCoTransform, DuckdbInput, DuckdbOutput, DuckdbTransform

DuckdbPlan: TypeAlias = DuckDBPyRelation | str

DuckdbEtlStep: TypeAlias = DuckdbInput | DuckdbTransform | DuckdbCoTransform | DuckdbOutput

DuckdbConfig = dict[str, str | bool | int | float | list[str]] | None

DuckdbFileFormat = Literal[
    "parquet",
    "csv",
    "json",
]

DuckdbWriteMode = Literal[
    "append",
    "overwrite",
    "overwrite_or_ignore",
]

DuckdbCompression = Literal[
    "uncompressed",
    "snappy",
    "zstd",
    "gzip",
    "brotli",
    "lz4",
    "lz4_raw",
]
