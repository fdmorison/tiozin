from __future__ import annotations

from duckdb import DuckDBPyRelation

from tiozin.api import Context
from tiozin.exceptions import RequiredArgumentError
from tiozin.utils import as_list, clear_dir, ensure_dir, trim_lower, trim_upper

from .. import DuckdbOutput
from ..typehints import DuckdbCompression, DuckdbPlan, DuckdbTiozinFileFormat, DuckdbWriteMode


class DuckdbFileOutput(DuckdbOutput):
    """
    Writes a DuckDB relation to files using DuckDB.

    This output writes DuckDBPyRelation data to disk in any format
    supported by DuckDB, such as Parquet, CSV, or JSON. Write behavior and
    options follow standard DuckDB semantics.

    For advanced and format-specific options, refer to DuckDB documentation at:

    https://duckdb.org/docs/data/overview

    Attributes:
        path:
            Target path where output files will be written.

        format:
            File format used for writing the data.

        mode:
            Write mode: ``"append"`` or ``"overwrite"``.

        partition_by:
            Column name or list of column names used to partition the output
            files.

        compression:
            Compression codec. Defaults to snappy.

        **options:
            Additional DuckDB writer options passed directly to the
            underlying write method.

    Examples:

        ```python
        DuckdbFileOutput(
            path="/data/events",
            format="parquet",
            mode="overwrite",
            partition_by=["date"],
            compression="snappy",
        )
        ```

        ```yaml
        outputs:
          - type: DuckdbFileOutput
            path: /data/events
            format: parquet
            mode: overwrite
            partition_by: ["date"]
            compression: snappy
        ```
    """

    def __init__(
        self,
        path: str = None,
        format: DuckdbTiozinFileFormat = None,
        mode: DuckdbWriteMode = None,
        partition_by: list[str] = None,
        compression: DuckdbCompression = None,
        **options,
    ) -> None:
        super().__init__(**options)
        RequiredArgumentError.raise_if_missing(
            path=path,
        )
        self.path = path if path.endswith("/") else f"{path}/"
        self.format = trim_lower(format or "parquet")
        self.mode = trim_upper(mode or "append")
        self.partition_by = as_list(partition_by, [])
        self.compression = trim_lower(compression or "snappy")

    def write(self, _: Context, data: DuckDBPyRelation) -> DuckdbPlan:
        """
        Builds a ``COPY TO`` statement that writes the relation using a data-lake-style layout.

        Output is always written to a directory, never to a single file. Data is emitted as one or
        more part files inside the target path, following a predictable naming pattern and using
        columnar storage with compression enabled by default.

        When ``partition_by`` is provided, data is written using Hive-style partitioning
        (``col=value/``). Otherwise, multiple output files may still be produced to allow parallel
        writes.

        This mirrors common conventions used by engines such as Spark: directory-based outputs,
        partition-aware layouts, and compressed part files, ensuring interoperability with
        downstream consumers.

        Finally, returns a SQL string to be executed lazily by the runner.
        """
        self.info(f"Writing {self.format} to {self.path}")

        if self.mode == "OVERWRITE":
            clear_dir(self.path)

        ensure_dir(self.path)

        args = {
            "FORMAT": self.format,
            "FILENAME_PATTERN": f"'part-{{i}}-{{uuidv7}}.{self.compression}'",
            "COMPRESSION": self.compression,
            self.mode: "1",
        }

        if self.partition_by:
            args["PARTITION_BY"] = f"({','.join(self.partition_by)})"
        else:
            args["PER_THREAD_OUTPUT"] = "true"

        for key, value in self.options.items():
            args[key.upper()] = value

        args_str = ",".join(f"{k} {v}" for k, v in args.items())
        return f"COPY {data.alias} TO '{self.path}' ({args_str})"
