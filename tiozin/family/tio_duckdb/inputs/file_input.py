from __future__ import annotations

from duckdb import DuckDBPyRelation

from tiozin.api import Context
from tiozin.exceptions import RequiredArgumentError
from tiozin.utils import as_list, trim_lower

from .. import DuckdbInput
from ..compose.assembly.read_builder import ReadBuilder
from ..typehints import DuckdbTiozinFileFormat, DuckdbTiozinReadMode


class DuckdbFileInput(DuckdbInput):
    """
    Reads files into a DuckDB relation using DuckDB.

    This input reads data from disk or external storage in any format supported by DuckDB,
    such as Parquet, CSV, JSON, or plain text. Read behavior and options follow standard
    DuckDB semantics.

    The format maps directly to a DuckDB ``read_<format>()`` table function, so any format
    supported by DuckDB (including extensions) works out of the box — e.g. ``"parquet"``,
    ``"csv"``, ``"json"``, ``"text"``, ``"xlsx"``, ``"blob"``, etc.

    Tiozin also provides convenience aliases that resolve to the appropriate DuckDB reader
    with sensible defaults:

    - tsv       → read_csv(delim='\\t')
    - jsonl     → read_ndjson()
    - txt       → read_text()
    - auto_csv  → read_csv_auto()
    - auto_json → read_json_auto()

    For advanced and format-specific options, refer to DuckDB documentation at:

    https://duckdb.org/docs/data/overview

    Attributes:
        path: Path or list of paths to the files or directories to read from.
        format: File format used for reading the data. Defaults to ``"parquet"``. Maps to the
            DuckDB ``read_<format>()`` table function. Accepts both native DuckDB formats and
            Tiozin aliases.
        hive_partitioning: Whether to interpret Hive-style partition directories
            (``col=value/``). Defaults to ``True``.
        union_by_name: Whether to unify schemas by column name when reading multiple files
            with potentially different structures. Defaults to ``True``.
        explode_filepath: When enabled, expands the input file path into multiple semantic
            columns: ``dirpath``, ``dirname``, ``filepath``, ``filename``, ``filestem``, and
            ``filetype``. For text and blob formats, also includes ``filesize``. While
            ``filesize`` is not derived directly from the file path, it is considered part of
            the minimal file structural context provided by this option. This option is
            intentionally scoped to file-level structure and does not include format-specific
            metadata (e.g. Parquet metadata).
        mode: How the read result is materialized in DuckDB. Defaults to ``"relation"`` (lazy).
            Other modes (``"table"``, ``"overwrite_table"``, ``"view"``, ``"temp_table"``,
            ``"temp_view"``) register the result under the step name.
        **options: Additional DuckDB reader options passed directly to the ``read_<format>()``
            function as named parameters.

    Examples:

        ```python
        DuckdbFileInput(
            path="/data/events",
            format="json",
            explode_filepath=True,
        )
        ```

        ```yaml
        inputs:
          - type: DuckdbFileInput
            path: /data/events
            format: json
            explode_filepath: true
        ```
    """

    def __init__(
        self,
        path: str | list[str] = None,
        format: DuckdbTiozinFileFormat = None,
        mode: DuckdbTiozinReadMode = None,
        hive_partitioning: bool = True,
        union_by_name: bool = True,
        explode_filepath: bool = False,
        **options,
    ) -> None:
        super().__init__(**options)
        RequiredArgumentError.raise_if_missing(
            path=path,
        )
        self.path = as_list(path)
        self.format = trim_lower(format) or "parquet"
        self.mode = trim_lower(mode) or "relation"
        self.hive_partitioning = hive_partitioning
        self.union_by_name = union_by_name
        self.explode_filepath = explode_filepath

    def read(self, _: Context) -> DuckDBPyRelation:
        self.info(f"Reading {self.format} from {self.path}")

        relation = (
            ReadBuilder(self.duckdb)
            .mode(self.mode, self.name)
            .format(self.format)
            .path(self.path)
            .with_hive_partitioning(self.hive_partitioning)
            .with_union_by_name(self.union_by_name)
            .with_explode_filepath(self.explode_filepath)
            .options(**self.options)
            .load()
        )

        return relation
