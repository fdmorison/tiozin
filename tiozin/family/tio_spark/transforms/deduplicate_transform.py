from pyspark.sql import Column, DataFrame, Window
from pyspark.sql import functions as sf

from tiozin.exceptions import TiozinInputError
from tiozin.utils import as_list, default

from .. import SparkTransform

KEEP_FIRST = "first"
KEEP_LAST = "last"
KEEP_OPTIONS = {KEEP_FIRST, KEEP_LAST}

DEFAULT_KEEP = KEEP_LAST

RANK_FIELD = "__tio_rank"


class SparkDeduplicateTransform(SparkTransform):
    """
    Removes duplicate rows from a Spark DataFrame, keeping one row per key.

    By default, an arbitrary row is kept for each key. Use `order_by` to sort rows
    within each key group and `keep` to choose the first or last row.

    Without `keys`, rows are compared across all fields, except those specified
    in `order_by`. This allows exact duplicates to be removed or, when ordering
    is specified, rows that differ only in the ordering fields.

    Deduplication without ordering is non-deterministic: if duplicate rows differ
    in other fields, the row kept may vary between runs.

    For the full guide and examples, refer to:

    https://github.com/fdmorison/tiozin/blob/main/docs/tio_spark/deduplicate-transform.md

    Attributes:
        keys:
            Field or list of fields used to identify duplicate rows. Rows with the
            same values in these fields belong to the same group. If omitted, all
            fields except those in `order_by` are used to identify duplicates.

        order_by:
            Field or list of fields used to sort rows within each group in
            ascending order. When comparing values, non-null values take
            precedence over nulls. If multiple rows have the same ordering values,
            an arbitrary row is kept. Add tie-breaker fields when needed.

        keep:
            Which row to keep after sorting: `first` keeps the row with the lowest
            ordering values, while `last` keeps the row with the highest.
            Defaults to `last` and requires `order_by`.

    Examples:

        Remove exact duplicate rows:

        ```python
        SparkDeduplicateTransform()
        ```

        ```yaml
        transforms:
          - kind: SparkDeduplicateTransform
            name: customers
        ```

        Remove duplicates, keeping the row with the latest `ingested_at`:

        ```yaml
        transforms:
          - kind: SparkDeduplicateTransform
            name: customers
            order_by: ingested_at
        ```

        Remove rows with the same `customer_id`, keeping an arbitrary row:

        ```yaml
        transforms:
          - kind: SparkDeduplicateTransform
            name: customers
            keys: customer_id
        ```

        Remove rows with the same `customer_id`, keeping the most recently updated:

        ```yaml
        transforms:
          - kind: SparkDeduplicateTransform
            name: customers
            keys: customer_id
            order_by: updated_at
        ```

        Keep the earliest updated row for each `customer_id`:

        ```yaml
        transforms:
          - kind: SparkDeduplicateTransform
            name: customers
            keys: customer_id
            order_by: updated_at
            keep: first
        ```

        Remove duplicates by `tenant_id` and `customer_id`, keeping the latest
        updated row and using the highest `sequence` to break ties:

        ```yaml
        transforms:
          - kind: SparkDeduplicateTransform
            name: customers
            keys: [tenant_id, customer_id]
            order_by: [updated_at, sequence]
            keep: last
        ```
    """

    def __init__(
        self,
        keys: str | list[str] = None,
        order_by: str | list[str] = None,
        keep: str = None,
        **options,
    ) -> None:
        super().__init__(**options)
        TiozinInputError.raise_if_not_in(
            keep,
            KEEP_OPTIONS,
            allow_none=True,
        ).raise_if(
            keep is not None and not order_by,
            "`keep` requires `order_by`",
        )

        self.keys = as_list(keys, [])
        self.order_by = as_list(order_by, [])
        self.keep = default(keep, DEFAULT_KEEP)

    def transform(self, data: DataFrame) -> DataFrame:
        if self.order_by:
            return self._deduplicate_ordered(data)
        return self._deduplicate_unordered(data)

    def _deduplicate_unordered(self, data: DataFrame) -> DataFrame:
        return data.dropDuplicates(self.keys or None)

    def _deduplicate_ordered(self, data: DataFrame) -> DataFrame:
        keys = self.keys or [field for field in data.columns if field not in self.order_by]
        window = Window.partitionBy(*keys).orderBy(*self._sort_order())
        return (
            data.withColumn(RANK_FIELD, sf.row_number().over(window))
            .where(sf.col(RANK_FIELD) == 1)
            .drop(RANK_FIELD)
        )

    def _sort_order(self) -> list[Column]:
        if self.keep == KEEP_LAST:
            return [sf.desc_nulls_last(field) for field in self.order_by]
        return [sf.asc_nulls_last(field) for field in self.order_by]
