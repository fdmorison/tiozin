import pytest
from pyspark.errors import AnalysisException
from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin.family.tio_spark import SparkSqlTransform
from tiozin.utils.runtime import tio_alias

# ============================================================================
# Testing SparkSqlTransform - Core Behavior
# ============================================================================


def test_transform_should_execute_sql_using_existing_view(spark_session: SparkSession):
    """
    This test simulates the canonical happy path of SparkSqlTransform inside
    a pipeline, where the SQL query operates on a view previously registered
    by an upstream step.

    It validates that SparkSqlTransform can execute SQL against existing
    catalog views without relying on the @self token.
    """
    # Arrange
    input = spark_session.createDataFrame(
        [
            (1, "Alice"),
            (2, "Bob"),
        ],
        schema="`id` INT, `name` STRING",
    )
    input.createOrReplaceTempView("customers")
    context = None

    # Act
    actual = SparkSqlTransform(
        name="sql_existing_view",
        query="SELECT * FROM customers",
    ).transform(context, input)

    # Assert
    expected = spark_session.createDataFrame(
        [
            (1, "Alice"),
            (2, "Bob"),
        ],
        schema="`id` INT, `name` STRING",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_execute_sql_using_multiple_existing_views(
    spark_session: SparkSession,
):
    """
    This test simulates a SQL transformation that operates on multiple
    pre-existing views registered in the Spark catalog by upstream steps.

    It validates that SparkSqlTransform can execute a SQL query that joins
    multiple existing views without relying on @self, which represents the
    canonical happy path for SQL-based composition in a pipeline.
    """
    # Arrange
    customers = spark_session.createDataFrame(
        [
            (1, "Alice"),
            (2, "Bob"),
        ],
        schema="`id` INT, `name` STRING",
    )
    orders = spark_session.createDataFrame(
        [
            (1, 100.0),
            (2, 50.0),
        ],
        schema="`customer_id` INT, `total` DOUBLE",
    )
    customers.createOrReplaceTempView("customers")
    orders.createOrReplaceTempView("orders")
    context = None

    # Act
    actual = SparkSqlTransform(
        name="sql_multiple_existing_views",
        query="""
            SELECT c.id, c.name, o.total
            FROM customers c
            JOIN orders o
              ON c.id = o.customer_id
        """,
    ).transform(context, customers)

    # Assert
    expected = spark_session.createDataFrame(
        [
            (1, "Alice", 100.0),
            (2, "Bob", 50.0),
        ],
        schema="`id` INT, `name` STRING, `total` DOUBLE",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_bind_single_dataframe_as_self(spark_session: SparkSession):
    """
    This test simulates the explicit use of the @self token as an input
    reference in the SQL query.

    It validates that SparkSqlTransform correctly exposes the current input
    DataFrame as a temporary view and allows it to be queried via @self.
    """
    # Arrange
    input = spark_session.createDataFrame(
        [
            (1, 100.0),
            (2, 50.0),
        ],
        schema="`id` INT, `total` DOUBLE",
    )
    tio_alias(input, "input")
    input.createOrReplaceTempView("input")

    # Act
    actual = SparkSqlTransform(
        name="sql_self",
        query="SELECT * FROM @self WHERE total > 80",
    ).transform(None, input)

    # Assert
    expected = spark_session.createDataFrame(
        [
            (1, 100.0),
        ],
        schema="`id` INT, `total` DOUBLE",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_bind_multiple_dataframes_as_self_sequence(spark_session: SparkSession):
    """
    This test simulates a multi-input SQL transformation where the primary
    input (@self) is joined with a secondary input (@self1).

    It validates that SparkSqlTransform correctly exposes multiple inputs
    to the SQL layer and allows them to be composed in a single query.
    """
    # Arrange
    customers = spark_session.createDataFrame(
        [
            (1, "Alice"),
            (2, "Bob"),
        ],
        schema="`id` INT, `name` STRING",
    )
    tio_alias(customers, "customers")
    customers.createOrReplaceTempView("customers")

    regions = spark_session.createDataFrame(
        [
            (1, "EU"),
            (2, "US"),
        ],
        schema="`id` INT, `region` STRING",
    )
    tio_alias(regions, "regions")
    regions.createOrReplaceTempView("regions")

    # Act
    actual = SparkSqlTransform(
        name="sql_multi_input",
        query="""
            SELECT c.id, c.name, r.region
            FROM @self c
            JOIN @self1 r ON c.id = r.id
        """,
    ).transform(None, customers, regions)

    # Assert
    expected = spark_session.createDataFrame(
        [
            (1, "Alice", "EU"),
            (2, "Bob", "US"),
        ],
        schema="`id` INT, `name` STRING, `region` STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_execute_sql_on_empty_dataframe(spark_session: SparkSession):
    """
    This test simulates the execution of a SQL transformation over an empty
    input DataFrame.

    It validates that SparkSqlTransform correctly propagates an empty input
    through SQL execution and returns an empty DataFrame with the expected
    schema.
    """
    # Arrange
    input = spark_session.createDataFrame(
        [],
        schema="`id` INT, `name` STRING",
    )
    tio_alias(input, "input")
    input.createOrReplaceTempView("input")

    # Act
    actual = SparkSqlTransform(
        name="sql_empty_input",
        query="SELECT * FROM @self",
    ).transform(None, input)

    # Assert
    expected = spark_session.createDataFrame(
        [],
        schema="`id` INT, `name` STRING",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_accept_args_parameter(spark_session: SparkSession):
    """
    This test simulates a parameterized SQL query using named arguments.

    It validates that SparkSqlTransform correctly binds runtime parameters
    to the SQL query and applies row-level filtering based on those values.
    """
    # Arrange
    input = spark_session.createDataFrame(
        [
            (1, "Alice", 100.0),
            (2, "Bob", 50.0),
        ],
        schema="`id` INT, `name` STRING, `total` DOUBLE",
    )
    tio_alias(input, "input")
    input.createOrReplaceTempView("input")

    # Act
    actual = SparkSqlTransform(
        name="sql_args",
        query="SELECT * FROM @self WHERE total > :min_total",
        args={"min_total": 80.0},
    ).transform(None, input)

    # Assert
    expected = spark_session.createDataFrame(
        [
            (1, "Alice", 100.0),
        ],
        schema="`id` INT, `name` STRING, `total` DOUBLE",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_remove_self_views_after_execution(spark_session: SparkSession):
    """
    This test simulates repeated execution of SparkSqlTransform within the same
    SparkSession.

    It validates that temporary self views created during execution are properly
    cleaned up, preventing catalog pollution and name collisions across steps.
    """
    # Arrange
    input = spark_session.createDataFrame(
        [(1,), (2,)],
        schema="`value` INT",
    )
    tio_alias(input, "input")
    input.createOrReplaceTempView("input")

    # Act
    SparkSqlTransform(
        name="sql_cleanup",
        query="SELECT * FROM @self",
    ).transform(None, input)

    # Assert
    with pytest.raises(AnalysisException):
        spark_session.sql("SELECT * FROM __self__").collect()


# ============================================================================
# Testing SparkSqlTransform - Failure Scenarios
# ============================================================================


def test_transform_should_fail_when_referenced_view_does_not_exist(spark_session: SparkSession):
    """
    This test simulates a failure scenario where the SQL query references
    a view that does not exist in the Spark catalog.

    It validates that SparkSqlTransform does not mask Spark analysis errors
    and propagates the failure to the caller.
    """
    # Arrange
    input = spark_session.createDataFrame(
        [(1,)],
        schema="`value` INT",
    )
    context = None

    # Act / Assert
    with pytest.raises(AnalysisException):
        SparkSqlTransform(
            name="sql_missing_view",
            query="SELECT * FROM does_not_exist",
        ).transform(context, input)


def test_transform_should_fail_when_sql_is_invalid(spark_session: SparkSession):
    """
    This test simulates a failure caused by an invalid SQL statement.

    It ensures that SparkSqlTransform fails fast and does not silently ignore
    SQL syntax errors.
    """
    # Arrange
    input = spark_session.createDataFrame(
        [(1,)],
        schema="`value` INT",
    )
    tio_alias(input, "input")
    input.createOrReplaceTempView("input")

    # Act / Assert
    with pytest.raises(AnalysisException):
        SparkSqlTransform(
            name="sql_invalid",
            query="SELECXXX * FROM @self",
        ).transform(None, input)


# ============================================================================
# Testing SparkSqlTransform - Catalog Resolution and Shadowing
# ============================================================================


def test_transform_should_shadow_existing_table_with_step_view(spark_session: SparkSession):
    """
    This test simulates a scenario where a Spark table already exists in the
    catalog with the same name as a view created by an upstream step.

    It validates that SparkSqlTransform gives precedence to the temporary view
    registered by the pipeline step, effectively shadowing the existing table
    during SQL execution.
    """
    # Arrange
    spark_session.sql("DROP TABLE IF EXISTS shadowed")
    spark_session.sql(
        """
        CREATE TABLE shadowed (
            id INT,
            name STRING
        )
        USING parquet
        """
    )
    spark_session.sql(
        """
        INSERT INTO shadowed VALUES
            (1, 'TABLE_ALICE'),
            (2, 'TABLE_BOB')
        """
    )
    viewdata = spark_session.createDataFrame(
        [
            (1, "VIEW_ALICE"),
            (2, "VIEW_BOB"),
        ],
        schema="`id` INT, `name` STRING",
    )
    viewdata.createOrReplaceTempView("shadowed")
    context = None

    # Act
    result = SparkSqlTransform(
        name="sql_shadowing",
        query="SELECT * FROM shadowed",
    ).transform(context, viewdata)

    # Assert
    actual = result
    expected = spark_session.createDataFrame(
        [
            (1, "VIEW_ALICE"),
            (2, "VIEW_BOB"),
        ],
        schema="`id` INT, `name` STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)
