from __future__ import annotations

from typing import Any, Self, get_args

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as sf

from tiozin.exceptions import RequiredArgumentError, TiozinInputError
from tiozin.utils import as_list, slugify

from ..typehints import TioSparkTableOutputMode

DEFAULT_WRITE_MODE = "append"


class TioSparkTableWriter:
    """
    Writes a DataFrame to a table registered in a catalog.

    `DataFrameWriterV2` writes as soon as a mode is called. This writer fixes
    that by being lazy: nothing is written until `save()` is called. Also, the
    table is created when it does not exist, whatever the mode.

    The fluent interface intentionally follows the classic Spark `DataFrameWriter`,
    with `format()`, `options()` and `mode()`, although the writer is implemented
    on top of `DataFrameWriterV2`.

    It also adds the `truncate`, `overwrite_partitions` and `merge` modes:

    - `append`: adds the rows to the table.
    - `truncate`: replaces all rows, keeping the table schema and properties.
    - `overwrite`: replaces all rows, replacing the table schema and properties.
    - `overwrite_partitions`: replaces only the partitions present in the DataFrame.
    - `merge`: updates the rows that match `keys` and inserts the others.

    Works with both classic and Spark Connect sessions.

    Args:
        df:
            DataFrame to write.

        table:
            Table name, qualified as `catalog.schema.table`.

    Examples:

        ```python
        TioSparkTableWriter(df, "my_catalog.default.sales")
            .mode("append")
            .save()
        ```

        ```python
        (
            TioSparkTableWriter(df, "my_catalog.default.customers")
            .format("delta")
            .mode("merge", keys=["customer_id"])
            .save()
        )
        ```
    """

    def __init__(self, df: DataFrame, table: str) -> None:
        self._df = df
        self._table = table
        self._writer = df.writeTo(table)
        self._mode: TioSparkTableOutputMode = DEFAULT_WRITE_MODE
        self._keys: list[str] = []

    def format(self, format: str) -> Self:
        """
        Sets the table format used when the table is created, such as `delta` or `iceberg`.
        """
        self._writer.using(format)
        return self

    def option(self, key: str, value: Any) -> Self:
        """
        Adds a write option.
        """
        self._writer.option(key, value)
        return self

    def options(self, **options) -> Self:
        """
        Adds write options.
        """
        self._writer.options(**options)
        return self

    def tableProperty(self, property: str, value: str) -> Self:
        """
        Adds a table property, such as `write.format.default` in Iceberg.

        Properties are set only when the table is created, or recreated by the
        `overwrite` mode. Other modes leave the properties of an existing table
        unchanged.
        """
        self._writer.tableProperty(property, value)
        return self

    def tableProperties(self, **properties) -> Self:
        """
        Adds several table properties at once, one per keyword argument.

        Property names often contain dots, so pass them by unpacking a dict:
        `tableProperties(**{"write.format.default": "parquet"})`. Each pair is
        added as in `tableProperty()`, so the same rules about when properties
        are set apply.
        """
        for property, value in properties.items():
            self._writer.tableProperty(property, value)
        return self

    def partitionedBy(self, col: Column, *cols: Column) -> Self:
        """
        Partitions the table by the given columns.
        """
        self._writer.partitionedBy(col, *cols)
        return self

    def mode(self, mode: TioSparkTableOutputMode, keys: str | list[str] = None) -> Self:
        """
        Sets how `save()` writes the table.

        Args:
            mode:
                Write mode, one of the modes described in the class docstring.

            keys:
                Column or list of columns that identify a row. Required by the
                `merge` mode and ignored by the others.

        Raises:
            TiozinInputError: If the mode is not supported.
            RequiredArgumentError: If the mode is `merge` and no keys are given.
        """
        modes = get_args(TioSparkTableOutputMode)
        TiozinInputError.raise_if(
            mode not in modes,
            f"Unsupported write mode: '{mode}'. Supported: {', '.join(modes)}",
        )
        RequiredArgumentError.raise_if(
            mode == "merge" and not keys,
            "`keys` is required by the `merge` mode",
        )
        self._mode = mode
        self._keys = as_list(keys, [])
        return self

    def save(self) -> None:
        """
        Writes the table using the configured mode.
        """
        spark = self._df.sparkSession

        match self._mode:
            case _ if not spark.catalog.tableExists(self._table):
                self._writer.create()
            case "append":
                self._writer.append()
            case "overwrite":
                self._writer.createOrReplace()
            case "truncate":
                self._writer.overwrite(sf.lit(True))
            case "overwrite_partitions":
                self._writer.overwritePartitions()
            case "merge":
                source = f"__merge_{slugify(self._table)}"
                condition = " AND ".join(f"target.{key} = source.{key}" for key in self._keys)
                self._df.createOrReplaceTempView(source)
                try:
                    spark.sql(
                        f"MERGE INTO {self._table} AS target "
                        f"USING {source} AS source "
                        f"ON {condition} "
                        "WHEN MATCHED THEN UPDATE SET * "
                        "WHEN NOT MATCHED THEN INSERT *"
                    )
                finally:
                    spark.catalog.dropTempView(source)
