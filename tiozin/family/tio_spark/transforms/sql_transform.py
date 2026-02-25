from typing import Any

from pyspark.sql import DataFrame

from tiozin.utils import bind_data_tokens, tio_alias, trim

from .. import SparkCoTransform

SELF_VIEW = "__self__"


class SparkSqlTransform(SparkCoTransform):
    """
    Executes a Spark SQL query against temporary views.

    Queries can reference views created by previous steps (by step name) or use
    the `@data` token to reference the current dataframe inputs.

    Input references:
        - `@data` or `@data0`: First input (the step's primary input)
        - `@data1`, `@data2`, ...: Additional inputs (for multi-input transforms)
        - `<step_name>`: Any view registered by a previous step

    Parameterized queries:
        Use named parameters with `:param_name` syntax and provide values via `args`.

    Example:
        ```yaml
        inputs:
            - kind: SparkFileInput
              name: customers
              path: data/customers

            - kind: SparkFileInput
              name: orders
              path: data/orders

        transforms:
            # Reference views by step name
            - kind: SparkSqlTransform
              name: customer_orders
              query: |-
                SELECT c.id, c.name, o.total
                FROM customers c
                JOIN orders o ON c.id = o.customer_id

            # Use @data to reference current input dataframe
            - kind: SparkSqlTransform
              name: high_value_orders
              query: SELECT * FROM @data WHERE total > :min_total
              args:
                min_total: 100

            # Chain transforms using @data
            - kind: SparkSqlTransform
              name: with_timestamp
              query: SELECT *, current_timestamp() AS created_at FROM @data
        ```
    """

    def __init__(self, query: str, args: dict[str, Any] | list[Any] = None, **options) -> None:
        super().__init__(**options)
        self.query = trim(query)
        self.args = args

    def transform(self, data: DataFrame, *others: DataFrame) -> DataFrame:
        query = bind_data_tokens(
            self.query,
            [tio_alias(data), *(tio_alias(other) for other in others)],
        )
        return self.spark.sql(query, args=self.args)
