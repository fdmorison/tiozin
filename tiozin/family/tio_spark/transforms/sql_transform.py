from typing import Any

from pyspark.sql import DataFrame

from tiozin import Context

from .. import SparkCoTransform

SELF_VIEW = "__self__"
SELF_TOKEN = "@self"


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
        self.query = query
        self.args = args

    def setup(self, context: Context, data: DataFrame, *others: DataFrame):
        data.createOrReplaceTempView(SELF_VIEW)
        data.createOrReplaceTempView(SELF_VIEW + "0")
        for i, other in enumerate(others, start=1):
            other.createOrReplaceTempView(f"{SELF_VIEW}{i}")

    def transform(self, context: Context, data: DataFrame, *others: DataFrame) -> DataFrame:
        query = self.query.replace(SELF_TOKEN, SELF_VIEW)
        return self.spark.sql(query, args=self.args)

    def teardown(self, context: Context, data: DataFrame, *others: DataFrame):
        spark = self.spark
        for i, _ in enumerate(others, start=1):
            spark.catalog.dropTempView(f"{SELF_VIEW}{i}")
        spark.catalog.dropTempView(SELF_VIEW + "0")
        spark.catalog.dropTempView(SELF_VIEW)
