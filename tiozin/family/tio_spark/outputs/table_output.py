from __future__ import annotations

import openlineage_sql
from pyspark.sql import DataFrame

from tiozin import Dataset, Datasets
from tiozin.exceptions import RequiredArgumentError, TiozinInputError
from tiozin.utils import as_list, default, trim, trim_lower

from .. import SparkOutput
from ..typehints import TioSparkTableOutputMode
from ..writers.table_writer import TioSparkTableWriter

DEFAULT_FORMAT = "iceberg"
DEFAULT_WRITE_MODE = "append"


class SparkTableOutput(SparkOutput):
    """
    Writes a Spark DataFrame to a table registered in a catalog.

    The table is addressed by name, so the catalog decides where the data is
    stored. This makes the output suitable for managed tables.

    The table is always created when it does not exist, whatever the mode.

    Args:
        table:
            Table name, qualified as `catalog.schema.table`. Names without a
            catalog or a schema are rejected. Required.

        format:
            Table format used when the table is created or recreated, such as
            `delta` or `iceberg`. Defaults to `iceberg`. Optional.

        mode:
            How the DataFrame is written to the table. Defaults to `append`. Optional.

            - `append`: adds the rows to the table.
            - `truncate`: replaces all rows, keeping the table schema and properties.
            - `overwrite`: replaces all rows, replacing the table schema and properties.
            - `overwrite_partitions`: replaces only the partitions present in the DataFrame.
            - `merge`: updates the rows that match `keys` and inserts the others.

        keys:
            Column or list of columns that identify a row. Required by the
            `merge` mode and ignored by the others.

        partition_by:
            Column name or list of column names used to partition the table
            when it is created or recreated. Optional.

        properties:
            Table properties set when the table is created or recreated, such as
            `{"write.format.default": "parquet"}`. Optional.

        **options:
            Additional write options passed directly to Spark.

    Examples:

        ```python
        SparkTableOutput(
            table="my_catalog.default.sales",
            format="delta",
            mode="append",
        )
        ```

        ```yaml
        outputs:
          - kind: SparkTableOutput
            table: my_catalog.default.sales
            format: delta
            mode: append
        ```

        ```yaml
        outputs:
          - kind: SparkTableOutput
            table: my_catalog.default.customers
            mode: merge
            keys: [customer_id]
        ```

        ```yaml
        outputs:
          - kind: SparkTableOutput
            table: my_catalog.default.events
            mode: overwrite_partitions
            partition_by: [country, day]
        ```
    """

    def __init__(
        self,
        table: str = None,
        format: str = None,
        mode: TioSparkTableOutputMode = None,
        keys: str | list[str] = None,
        partition_by: str | list[str] = None,
        properties: dict[str, str] = None,
        **options,
    ) -> None:
        super().__init__(**options)
        RequiredArgumentError.raise_if_missing(
            table=table,
        )
        TiozinInputError.raise_if(
            trim(table).count(".") != 2,
            f"Table must be qualified as `catalog.schema.table`: '{table}'",
        )
        self.table = trim(table)
        self.format = trim_lower(default(format, DEFAULT_FORMAT))
        self.mode = trim_lower(default(mode, DEFAULT_WRITE_MODE))
        self.keys = as_list(keys, [])
        self.partition_by = as_list(partition_by, [])
        self.properties = properties or {}

    def external_datasets(self) -> Datasets:
        lineage = openlineage_sql.parse([f"SELECT * FROM {self.table}"], dialect="spark")
        return Datasets(
            outputs=[Dataset.catalog_table(t.database, t.schema, t.name) for t in lineage.in_tables]
        )

    def write(self, data: DataFrame) -> TioSparkTableWriter:
        self.info(f"Writing table `{self.table}` with mode `{self.mode}`")

        writer = TioSparkTableWriter(data, self.table)

        if self.partition_by:
            writer = writer.partitionedBy(*self.partition_by)

        return (
            writer.format(self.format)
            .options(**self.options)
            .tableProperties(**self.properties)
            .mode(self.mode, keys=self.keys)
        )
