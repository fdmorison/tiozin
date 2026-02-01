from __future__ import annotations

from duckdb import DuckDBPyRelation

from tiozin.api import Context, conventions
from tiozin.exceptions import InvalidInputError, RequiredArgumentError
from tiozin.utils import as_list, trim_lower

from .. import DuckdbInput
from ..typehints import DuckdbFileFormat


class DuckdbFileInput(DuckdbInput):
    """
    Reads files into a DuckDB relation using DuckDB.

    This input reads data from disk or external storage in any format supported
    by DuckDB, such as Parquet, CSV, JSON, or plain text. Read behavior and
    options follow standard DuckDB semantics.

    For advanced and format-specific options, refer to DuckDB documentation at:

    https://duckdb.org/docs/data/overview

    Attributes:
        path:
            Path or list of paths to the files or directories to read from.

        format:
            File format used for reading the data. Defaults to ``"parquet"``.

        hive_partitioning:
            Whether to interpret Hive-style partition directories
            (``col=value/``). Defaults to ``True``. Not supported for the
            ``"text"`` format.

        include_file_metadata:
            Whether to include input file metadata columns in the relation.
            When enabled, adds ``filesize``, ``dirpath``, ``dirname``,
            ``filename``, ``filestem``, and ``filesuffix``.

        **options:
            Additional DuckDB reader options passed directly to DuckDB.
            Not supported for the ``"text"`` format.

    Examples:

        ```python
        DuckdbFileInput(
            path="/data/events",
            format="json",
            include_file_metadata=True,
        )
        ```

        ```yaml
        inputs:
          - type: DuckdbFileInput
            path: /data/events
            format: json
            include_file_metadata: true
        ```
    """

    def __init__(
        self,
        path: str | list[str] = None,
        format: DuckdbFileFormat = None,
        hive_partitioning: bool = True,
        include_file_metadata: bool = False,
        **options,
    ) -> None:
        super().__init__(**options)
        RequiredArgumentError.raise_if_missing(
            path=path,
        )
        self.path = as_list(path)
        self.format = trim_lower(format or "parquet")
        self.hive_partitioning = hive_partitioning
        self.include_file_metadata = include_file_metadata

    def read(self, _: Context) -> DuckDBPyRelation:
        self.info(f"Reading {self.format} from {self.path}")

        match self.format:
            case "csv":
                relation = self.duckdb.read_csv(
                    self.path,
                    filename=self.include_file_metadata,
                    hive_partitioning=self.hive_partitioning,
                    **self.options,
                )
            case "parquet":
                relation = self.duckdb.read_parquet(
                    self.path,
                    filename=self.include_file_metadata,
                    hive_partitioning=self.hive_partitioning,
                    **self.options,
                )
            case "json":
                relation = self.duckdb.read_json(
                    self.path,
                    filename=self.include_file_metadata,
                    hive_partitioning=self.hive_partitioning,
                    **self.options,
                )
            case "text":
                filemeta = "filename," if self.include_file_metadata else ""
                relation = self.duckdb.sql(f"""
                    SELECT {filemeta}content AS {conventions.CONTENT_COLUMN}
                    FROM read_text({self.path})
                """)

            case _:
                raise InvalidInputError(f"DuckDB does not support reading `{self.format}` inputs.")

        if self.include_file_metadata:
            relation = self.duckdb.sql(f"""
            SELECT
                * EXCLUDE (filename),
                parse_dirpath(filename)                 AS {conventions.DIRPATH_COLUMN},
                parse_filename(parse_dirpath(filename)) AS {conventions.DIRNAME_COLUMN},
                parse_filename(filename)                AS {conventions.FILENAME_COLUMN},
                parse_filename(filename, true)          AS {conventions.FILESTEM_COLUMN},
                CASE
                    WHEN strpos(parse_filename(filename), '.') = 0 THEN ''
                    ELSE reverse(split_part(reverse(parse_filename(filename)), '.', 1))
                END                                     AS {conventions.FILETYPE_COLUMN}
            FROM relation
            """)

        return relation
