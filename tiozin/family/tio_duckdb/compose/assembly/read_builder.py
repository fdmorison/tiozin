from __future__ import annotations

from typing import Any

from duckdb import DuckDBPyConnection, DuckDBPyRelation

from tiozin.api import conventions
from tiozin.exceptions import RequiredArgumentError
from tiozin.utils.helpers import as_list

from .read_spec import ReadSpec

_VALID_MODES = {"relation", "temp_view", "view", "table", "temp_table", "overwrite_table"}


class ReadBuilder:
    """
    Fluent builder for DuckDB file reader queries.

    Resolves Tiozin format aliases and auto-detect variants eagerly in :meth:`format`. Handles
    parameterless readers (``text``, ``blob``), filepath expansion, and delegates base reading
    to ``ReadSpec``.

    When ``with_explode_filepath()`` is enabled, the input file path is expanded into multiple
    semantic columns, including:

    - dirpath
    - dirname
    - filepath
    - filename
    - filestem
    - filetype

    It also includes the ``filesize`` column. While ``filesize`` is not derived directly from
    the file path, it is considered part of the minimal file structural context provided by
    this option.

    This option is intentionally scoped to file-level structure and does not include
    format-specific metadata (e.g. Parquet metadata).

    The load mode controls how the result is materialized:

    - ``load()`` (default) — returns the relation as-is
    - ``mode("temp_view", name).load()`` — registers a named temporary view
    - ``mode("table", name).load()`` — creates a persistent table
    - ``mode("view", name).load()`` — creates a persistent view
    - ``mode("temp_table", name).load()`` — creates a temporary table
    - ``mode("overwrite_table", name).load()`` — creates or replaces a persistent table

    Examples::

        >>> ReadBuilder(conn).format("csv").path("/data/file.csv").load()
        <DuckDBPyRelation>

        >>> (
        ...     ReadBuilder(conn)
        ...     .format("tsv")
        ...     .path("/data/file.tsv")
        ...     .with_options(header=True)
        ...     .with_explode_filepath()
        ...     .mode("table", "my_table")
        ...     .load()
        ... )
    """

    def __init__(self, conn: DuckDBPyConnection) -> None:
        self._conn = conn
        self._path: list[str] = []
        self._load_mode: str = "relation"
        self._format: str = "parquet"
        self._format_options: dict[str, Any] = {}
        self._options: dict[str, Any] = {}
        self._explode_filepath: bool = False
        self._name: str | None = None

    def format(self, format: str) -> ReadBuilder:
        format, format_options = {
            "tsv": ("csv", {"delim": "\t"}),
            "jsonl": ("ndjson", {}),
            "txt": ("text", {}),
            "auto_csv": ("csv_auto", {}),
            "auto_json": ("json_auto", {}),
        }.get(format, (format, {}))
        self._format = format
        self._format_options = dict(format_options)
        return self

    def path(self, path: str | list[str]) -> ReadBuilder:
        self._path.extend(as_list(path))
        return self

    def options(self, **options) -> ReadBuilder:
        self._options |= options
        return self

    def with_hive_partitioning(self, enabled: bool = True) -> ReadBuilder:
        self._options["hive_partitioning"] = enabled
        return self

    def with_union_by_name(self, enabled: bool = True) -> ReadBuilder:
        self._options["union_by_name"] = enabled
        return self

    def with_explode_filepath(self, enabled: bool = True) -> ReadBuilder:
        self._options["filename"] = enabled
        self._explode_filepath = enabled
        return self

    def mode(self, mode: str, name: str) -> ReadBuilder:
        self._load_mode = mode
        self._name = name
        return self

    def to_relation(self) -> DuckDBPyRelation:
        RequiredArgumentError.raise_if_missing(
            conn=self._conn,
            path=self._path,
            load_mode=self._load_mode,
            format=self._format,
        ).raise_if(
            self._load_mode not in _VALID_MODES,
            f"Load mode requires one of {', '.join(_VALID_MODES)}. But got: {self._load_mode}.",
        ).raise_if(
            self._load_mode != "relation" and not self._name,
            "A name must be provided when using load modes other than 'relation'.",
        )

        options = {}
        columns = ["*"]

        if self._format in {"text", "blob"}:
            columns = [f"content AS {conventions.CONTENT_COLUMN}"]
            if self._explode_filepath:
                columns.append(f"size AS {conventions.FILESIZE_COLUMN}")
                columns.append("filename")
        else:
            options.update(self._format_options)
            options.update(self._options)

        relation = ReadSpec(
            format=self._format,
            path=self._path,
            options=options,
            columns=columns,
        ).to_relation(self._conn)

        if self._explode_filepath:
            relation = relation.project(
                "* EXCLUDE (filename),"
                f"parse_dirpath(filename)                 AS {conventions.DIRPATH_COLUMN},"
                f"parse_filename(parse_dirpath(filename)) AS {conventions.DIRNAME_COLUMN},"
                f"filename                                AS {conventions.FILEPATH_COLUMN},"
                f"parse_filename(filename)                AS {conventions.FILENAME_COLUMN},"
                f"parse_filename(filename, true)          AS {conventions.FILESTEM_COLUMN},"
                "CASE"
                "  WHEN strpos(parse_filename(filename), '.') = 0 THEN ''"
                "  ELSE reverse(split_part(reverse(parse_filename(filename)), '.', 1))"
                f"END AS {conventions.FILETYPE_COLUMN}"
            )

        return relation

    def load(self) -> DuckDBPyRelation:
        relation = self.to_relation()

        match self._load_mode:
            case "view":
                relation.create_view(self._name, replace=True)
                return self._conn.view(self._name)
            case "table":
                relation.create(self._name)
                return self._conn.table(self._name)
            case "overwrite_table":
                self._conn.sql(f"CREATE OR REPLACE TABLE {self._name} AS {relation.sql_query()}")
                return self._conn.table(self._name)
            case "temp_view":
                self._conn.register(self._name, relation)
                return relation
            case "temp_table":
                self._conn.sql(
                    f"CREATE OR REPLACE TEMP TABLE {self._name} AS {relation.sql_query()}"
                )
                return self._conn.table(self._name)
            case _:
                return relation
