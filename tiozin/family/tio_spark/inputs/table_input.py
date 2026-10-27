from __future__ import annotations

from datetime import date, datetime

import openlineage_sql
from pyspark.sql import DataFrame

from tiozin import Dataset, Datasets
from tiozin.exceptions import TiozinInputError
from tiozin.utils import as_list, trim

from .. import SparkInput


class SparkTableInput(SparkInput):
    """
    Reads a table registered in a catalog or executes a SQL query.

    Provide either `table` or `query`, depending on how the data should be read.
    Use `query` for more complex reads, such as joins across tables.

    `version` and `timestamp` support historical reads when the table format
    allows it. They apply only to `table` and cannot be used together.

    Args:
        table:
            Table name, optionally qualified as `catalog.schema.table`.
            Mutually exclusive with `query`.

        query:
            SQL query to read with. Mutually exclusive with `table`.

        columns:
            Column or list of columns to read. Defaults to all columns. Optional.

        where:
            SQL filter applied to the rows, such as `day >= '2026-01-01'`. Optional.

        version:
            Table version to read. Applies only to `table` and is mutually
            exclusive with `timestamp`. Optional.

        timestamp:
            Point in time to read the table at. Applies only to `table` and is
            mutually exclusive with `version`. Optional.

        **options:
            Additional reader options passed directly to Spark. Not applied
            when reading with `query`, `version` or `timestamp`.

    Examples:

        ```python
        SparkTableInput(
            table="my_catalog.default.sales",
            columns=["order_id", "amount"],
            where="day >= '2026-01-01'",
        )
        ```

        ```yaml
        inputs:
          - kind: SparkTableInput
            query: |
              SELECT o.order_id, o.amount, c.segment
              FROM sales o
              JOIN customers c USING (customer_id)
            where: day >= '2026-01-01'
        ```
    """

    def __init__(
        self,
        table: str = None,
        query: str = None,
        columns: str | list[str] = None,
        where: str = None,
        version: int | str = None,
        timestamp: str | date | datetime = None,
        **options,
    ) -> None:
        super().__init__(**options)
        TiozinInputError.raise_if(
            not table and not query,
            "Either `table` or `query` must be provided",
        )
        TiozinInputError.raise_if(
            table and query,
            "`table` and `query` are mutually exclusive",
        )
        TiozinInputError.raise_if(
            version is not None and timestamp,
            "`version` and `timestamp` are mutually exclusive",
        )
        TiozinInputError.raise_if(
            query and (version is not None or timestamp),
            "`version` and `timestamp` apply only to `table`",
        )
        self.table = trim(table)
        self.query = trim(query)
        self.columns = as_list(columns, [])
        self.where = trim(where)
        self.version = version
        self.timestamp = trim(str(timestamp)) if timestamp else None

    def external_datasets(self) -> Datasets:
        lineage = openlineage_sql.parse(
            [self.query or f"SELECT * FROM {self.table}"],
            dialect="spark",
        )

        if lineage.errors:
            self.warning(f"Could not extract the tables read: {lineage.errors}")

        return Datasets(
            inputs=[Dataset.catalog_table(t.database, t.schema, t.name) for t in lineage.in_tables]
        )

    def read(self) -> DataFrame:
        spark = self.spark

        if self.query:
            self.info("Reading tables with a SQL query")
            data = spark.sql(self.query)
        else:
            self.info(f"Reading table `{self.table}`")
            if self.version is not None:
                data = spark.sql(f"SELECT * FROM {self.table} VERSION AS OF {self.version}")
            elif self.timestamp:
                data = spark.sql(f"SELECT * FROM {self.table} TIMESTAMP AS OF '{self.timestamp}'")
            else:
                data = spark.read.options(**self.options).table(self.table)

        if self.where:
            data = data.where(self.where)

        if self.columns:
            data = data.select(*self.columns)

        return data
