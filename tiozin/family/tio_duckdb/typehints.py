from typing import Literal, TypeAlias

from duckdb import DuckDBPyRelation

from .bases import DuckdbCoTransform, DuckdbInput, DuckdbOutput, DuckdbTransform

DuckdbPlan: TypeAlias = DuckDBPyRelation | str

DuckdbEtlStep: TypeAlias = DuckdbInput | DuckdbTransform | DuckdbCoTransform | DuckdbOutput

DuckdbConfig = dict[str, str | bool | int | float | list[str]] | None

DuckdbTiozinFileFormat = Literal[
    # Standard DuckDB formats
    "parquet",
    "csv",
    "json",
    "ndjson",
    "text",
    "blob",
    "xlsx",
    # Tiozin-specific formats
    "tsv",
    "jsonl",
    "txt",
    "auto_csv",
    "auto_json",
]

DuckdbTiozinReadMode = Literal[
    "relation",
    "temp_view",
    "view",
    "table",
    "temp_table",
    "overwrite_table",
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
