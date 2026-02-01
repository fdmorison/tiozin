from typing import Any

from pyspark.sql import DataFrame

from tiozin import Context
from tiozin.utils import bind_self_tokens, tio_alias, trim

from .. import SparkCoTransform

SELF_VIEW = "__self__"


class SparkSqlTransform(SparkCoTransform):
    """
    Executes a Spark SQL query against temporary views.

    Queries can reference views created by previous steps (by step name) or use
    the `@self` token to reference the current dataframe inputs.

    Input references:
        - `@self` or `@self0`: First input (the step's primary input)
        - `@self1`, `@self2`, ...: Additional inputs (for multi-input transforms)
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

            # Use @self to reference current input dataframe
            - kind: SparkSqlTransform
              name: high_value_orders
              query: SELECT * FROM @self WHERE total > :min_total
              args:
                min_total: 100

            # Chain transforms using @self
            - kind: SparkSqlTransform
              name: with_timestamp
              query: SELECT *, current_timestamp() AS created_at FROM @self
        ```
    """

    def __init__(self, query: str, args: dict[str, Any] | list[Any] = None, **options) -> None:
        super().__init__(**options)
        self.query = trim(query)
        self.args = args

    def transform(self, _: Context, data: DataFrame, *others: DataFrame) -> DataFrame:
        query = bind_self_tokens(
            self.query,
            [tio_alias(data), *(tio_alias(other) for other in others)],
        )
        return self.spark.sql(query, args=self.args)
