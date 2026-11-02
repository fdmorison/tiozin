from __future__ import annotations

from typing import Any, Self, get_args

from pyspark.sql import Column, DataFrame, DataFrameWriterV2
from pyspark.sql import functions as sf

from tiozin.exceptions import RequiredArgumentError, TiozinInputError
from tiozin.utils import as_list

from ..functions import merge_into, to_partition_column
from ..typehints import TioSparkTableOutputMode

DEFAULT_WRITE_MODE = "append"
DEFAULT_TABLE_FORMAT = "iceberg"
ICEBERG_FORMAT = "iceberg"
ICEBERG_ACCEPT_ANY_SCHEMA = "write.spark.accept-any-schema"
RECREATE_MODES = ("overwrite", "drop_overwrite")


class TioSparkSimpleTableWriter:
    """
    Writes a DataFrame to a table registered in a catalog.

    `DataFrameWriterV2` writes as soon as a mode is called. This writer fixes
    that by being lazy: nothing is written until `save()` is called. Also, the
    table is created when it does not exist, whatever the mode.

    The fluent interface intentionally follows the classic Spark `DataFrameWriter`,
    with `format()`, `options()` and `mode()`, although the writer is implemented
    on top of `DataFrameWriterV2`.

    It also adds the `truncate`, `drop_overwrite`, `overwrite_partitions` and `merge` modes:

    - `append`: adds the rows to the table.
    - `truncate`: replaces all rows, preserving the table definition and history
    - `overwrite`: replaces all rows, replacing the table definition, but keeping the history.
    - `drop_overwrite`: drops the table and creates it again, losing the history.
    - `overwrite_partitions`: replaces only the partitions present in the DataFrame.
    - `merge`: updates the rows that match the keys set by `onMergeInto()` and inserts the others.

    Works with both classic and Spark Connect sessions.

    Args:
        df:
            DataFrame to write.

        table:
            Table name, qualified as `catalog.schema.table`.

    Examples:

        ```python
        TioSparkSimpleTableWriter(df, "my_catalog.default.sales")
            .mode("append")
            .save()
        ```

        ```python
        (
            TioSparkSimpleTableWriter(df, "my_catalog.default.customers")
            .format("delta")
            .mode("merge")
            .onMergeInto(keys="customer_id", exclude_fields="created_at")
            .save()
        )
        ```
    """

    def __init__(self, df: DataFrame, table: str) -> None:
        self._df = df
        self._table = table
        self._mode: TioSparkTableOutputMode = DEFAULT_WRITE_MODE
        self._merge_keys: list[str] = []
        self._merge_exclude_fields: list[str] = []
        self._format: str = DEFAULT_TABLE_FORMAT
        self._properties: dict[str, str] = {}
        self._options: dict[str, Any] = {}
        self._partition_by: list[str | Column] = []
        self._schema_evolution: bool = False

    def format(self, format: str) -> Self:
        """
        Sets the table format used when the table is created, such as `delta` or `iceberg`.
        """
        self._format = format
        return self

    def option(self, key: str, value: Any) -> Self:
        """
        Adds a write option.
        """
        self._options[key] = value
        return self

    def options(self, **options) -> Self:
        """
        Adds write options.
        """
        self._options.update(options)
        return self

    def tableProperty(self, property: str, value: str) -> Self:
        """
        Adds a table property, such as `write.format.default` in Iceberg.

        Properties are set only when the table is created, or recreated by the
        `overwrite` and `drop_overwrite` modes. Other modes leave the properties
        of an existing table unchanged.
        """
        self._properties[property] = value
        return self

    def tableProperties(self, **properties) -> Self:
        """
        Adds several table properties at once, one per keyword argument.

        Property names often contain dots, so pass them by unpacking a dict:
        `tableProperties(**{"write.format.default": "parquet"})`. Each pair is
        added as in `tableProperty()`, so the same rules about when properties
        are set apply.
        """
        self._properties.update(properties)
        return self

    def partitionedBy(self, col: str | Column, *cols: str | Column) -> Self:
        """
        Partitions the table by the given columns, applied when the table is
        created or recreated. Also accepts the transform functions `years`,
        `months`, `days`, `hours`, and `bucket`.
        """
        self._partition_by = [col, *cols]
        return self

    def withSchemaEvolution(self) -> Self:
        """
        Adds the new DataFrame columns to an existing table before the write.
        """
        self._schema_evolution = True
        return self

    def mode(self, mode: TioSparkTableOutputMode) -> Self:
        """
        Sets how `save()` writes the table.

        Args:
            mode:
                Write mode, one of the modes described in the class docstring.

        Raises:
            TiozinInputError: If the mode is not supported.
        """
        modes = get_args(TioSparkTableOutputMode)
        TiozinInputError.raise_if(
            mode not in modes,
            f"Unsupported write mode: '{mode}'. Supported: {', '.join(modes)}",
        )
        self._mode = mode
        return self

    def onMergeInto(
        self,
        keys: str | list[str] = None,
        exclude_fields: str | list[str] = None,
    ) -> Self:
        """
        Sets how the `merge` mode matches and updates rows. Ignored by other modes.

        Args:
            keys:
                Column or list of columns that identify a row. Required by the
                `merge` mode.

            exclude_fields:
                Column or list of columns excluded from updates, such as
                `created_at`. They are still written when a row is inserted.
                Nested fields are not supported.
        """
        self._merge_keys = as_list(keys, [])
        self._merge_exclude_fields = as_list(exclude_fields, [])
        return self

    def save(self) -> None:
        """
        Writes the table using the configured mode.

        Mode names differ from the `DataFrameWriterV2` methods on purpose. Spark calls
        `replace` what is really an `overwrite`, since neither rows nor table definition
        are preserved, and `overwrite` what is really a `truncate`, since the table
        definition is preserved but rows aren't.

        `replace()` fails on Delta up to 3.3.2 with Spark 3.5.6+ (delta-io/delta#4671).
        The `drop_overwrite` mode avoids it, at the cost of losing the history.

        Raises:
            RequiredArgumentError: If the mode is `merge` and no keys are given.
            TiozinInputError: If the mode is `merge` and `exclude_fields` has a
                name that is not a top-level column of the DataFrame.
        """
        RequiredArgumentError.raise_if(
            self._mode == "merge" and not self._merge_keys,
            "`keys` is required by the `merge` mode, set it with `onMergeInto()`",
        )
        TiozinInputError.raise_if(
            self._mode == "merge" and not set(self._merge_exclude_fields) <= set(self._df.columns),
            f"`exclude_fields` must name top-level DataFrame columns: {self._merge_exclude_fields}",
        )
        spark = self._df.sparkSession
        table_exists = spark.catalog.tableExists(self._table)
        writer = self._build_writer()

        if not table_exists:
            writer.create()
            return

        if self._schema_evolution and self._mode not in RECREATE_MODES:
            self._evolve_schema()

        match self._mode:
            case "append":
                writer.append()
            case "overwrite":
                writer.replace()
            case "drop_overwrite":
                spark.sql(f"DROP TABLE {self._table}")
                writer.create()
            case "truncate":
                writer.overwrite(sf.lit(True))
            case "overwrite_partitions":
                writer.overwritePartitions()
            case "merge":
                merge_into(self._df, self._table, self._merge_keys, self._merge_exclude_fields)

    def _build_writer(self) -> DataFrameWriterV2:
        writer = (
            self._df.writeTo(self._table)
            .using(self._format)
            .option("check-ordering", "false")
            .options(**self._options)
        )

        if self._partition_by:
            writer = writer.partitionedBy(*[to_partition_column(c) for c in self._partition_by])

        for property, value in self._properties.items():
            writer = writer.tableProperty(property, value)

        return writer

    def _evolve_schema(self) -> None:
        spark = self._df.sparkSession

        if self._df.schema == spark.table(self._table).schema:
            return

        accepts_any_schema = bool(
            spark.sql(f"SHOW TBLPROPERTIES {self._table}")
            .filter(f"key = '{ICEBERG_ACCEPT_ANY_SCHEMA}' AND value = 'true'")
            .first()
        )

        toggle_property = self._format == ICEBERG_FORMAT and not accepts_any_schema

        if toggle_property:
            spark.sql(
                f"ALTER TABLE {self._table} "
                f"SET TBLPROPERTIES ('{ICEBERG_ACCEPT_ANY_SCHEMA}'='true')"
            )
        try:
            (
                spark.createDataFrame([], self._df.schema)
                .writeTo(self._table)
                .option("mergeSchema", "true")
                .option("check-ordering", "false")
                .append()
            )
        finally:
            if toggle_property:
                spark.sql(
                    f"ALTER TABLE {self._table} UNSET TBLPROPERTIES ('{ICEBERG_ACCEPT_ANY_SCHEMA}')"
                )
