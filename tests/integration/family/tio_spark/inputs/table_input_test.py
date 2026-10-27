import os
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlparse

import pytest
from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin.exceptions import TiozinInputError
from tiozin.family.tio_spark import SparkTableInput

# ============================================================================
# Testing SparkTableInput - Reading
# ============================================================================


def test_input_should_read_table(spark: SparkSession):
    """
    Happy path: the input reads every row and column of a catalog table.
    """
    # Arrange
    target_table = "spark_catalog.default.table_input_read"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            ('lorem', 1),
            ('ipsum', 2)
        AS t(word, count)
        """
    )

    # Act
    result = SparkTableInput(
        name="test",
        table=target_table,
    ).read()

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            ("lorem", 1),
            ("ipsum", 2),
        ],
        schema="word STRING, count INT",
    )
    assertDataFrameEqual(actual, expected)


def test_input_should_read_query(spark: SparkSession):
    """
    Reads the result of a SQL query, such as a join across two tables.
    """
    # Arrange
    sales_table = "spark_catalog.default.table_input_query_sales"
    customers_table = "spark_catalog.default.table_input_query_customers"
    spark.sql(
        f"""
        CREATE TABLE {sales_table} USING delta
        AS SELECT * FROM VALUES
            (10, 1, 100),
            (20, 2, 200)
        AS t(order_id, customer_id, amount)
        """
    )
    spark.sql(
        f"""
        CREATE TABLE {customers_table} USING delta
        AS SELECT * FROM VALUES
            (1, 'retail'),
            (2, 'wholesale')
        AS t(customer_id, segment)
        """
    )

    # Act
    result = SparkTableInput(
        name="test",
        query=f"""
            SELECT s.order_id, s.amount, c.segment
            FROM {sales_table} s
            JOIN {customers_table} c USING (customer_id)
        """,
    ).read()

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (10, 100, "retail"),
            (20, 200, "wholesale"),
        ],
        schema="order_id INT, amount INT, segment STRING",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# Testing SparkTableInput - Columns and Filters
# ============================================================================


def test_input_should_read_selected_columns(spark: SparkSession):
    # Arrange
    target_table = "spark_catalog.default.table_input_columns"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            (1, 'lorem', 'BR'),
            (2, 'ipsum', 'US')
        AS t(id, word, region)
        """
    )

    # Act
    result = SparkTableInput(
        name="test",
        table=target_table,
        columns=["id", "word"],
    ).read()

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "lorem"),
            (2, "ipsum"),
        ],
        schema="id INT, word STRING",
    )
    assertDataFrameEqual(actual, expected)


def test_input_should_filter_rows(spark: SparkSession):
    # Arrange
    target_table = "spark_catalog.default.table_input_where"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            (1, 'lorem', DATE'2025-12-31'),
            (2, 'ipsum', DATE'2026-01-01')
        AS t(id, word, day)
        """
    )

    # Act
    result = SparkTableInput(
        name="test",
        table=target_table,
        where="day >= '2026-01-01'",
    ).read()

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (2, "ipsum", date(2026, 1, 1)),
        ],
        schema="id INT, word STRING, day DATE",
    )
    assertDataFrameEqual(actual, expected)


def test_input_should_filter_rows_on_column_not_read(spark: SparkSession):
    """
    The filter can reference a column that is not listed in `columns`.
    """
    # Arrange
    target_table = "spark_catalog.default.table_input_where_unread_column"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            (1, 'lorem', DATE'2025-12-31'),
            (2, 'ipsum', DATE'2026-01-01')
        AS t(id, word, day)
        """
    )

    # Act
    result = SparkTableInput(
        name="test",
        table=target_table,
        columns=["id", "word"],
        where="day >= '2026-01-01'",
    ).read()

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (2, "ipsum"),
        ],
        schema="id INT, word STRING",
    )
    assertDataFrameEqual(actual, expected)


def test_input_should_read_selected_columns_from_query(spark: SparkSession):
    # Arrange
    target_table = "spark_catalog.default.table_input_query_columns"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            (1, 'lorem', 'BR'),
            (2, 'ipsum', 'US')
        AS t(id, word, region)
        """
    )

    # Act
    result = SparkTableInput(
        name="test",
        query=f"SELECT * FROM {target_table}",
        columns=["id", "word"],
    ).read()

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "lorem"),
            (2, "ipsum"),
        ],
        schema="id INT, word STRING",
    )
    assertDataFrameEqual(actual, expected)


def test_input_should_filter_query_rows(spark: SparkSession):
    # Arrange
    target_table = "spark_catalog.default.table_input_query_where"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            (1, 'lorem', DATE'2025-12-31'),
            (2, 'ipsum', DATE'2026-01-01')
        AS t(id, word, day)
        """
    )

    # Act
    result = SparkTableInput(
        name="test",
        query=f"SELECT * FROM {target_table}",
        where="day >= '2026-01-01'",
    ).read()

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (2, "ipsum", date(2026, 1, 1)),
        ],
        schema="id INT, word STRING, day DATE",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# Testing SparkTableInput - Time Travel
# ============================================================================


def test_input_should_read_table_at_version(spark: SparkSession):
    # Arrange
    target_table = "spark_catalog.default.table_input_at_version"
    spark.sql(f"CREATE TABLE {target_table} (word STRING, count INT) USING delta")
    spark.sql(f"INSERT INTO {target_table} VALUES ('lorem', 1)")
    spark.sql(f"INSERT INTO {target_table} VALUES ('ipsum', 2)")

    # Act
    result = SparkTableInput(
        name="test",
        table=target_table,
        version=1,
    ).read()

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            ("lorem", 1),
        ],
        schema="word STRING, count INT",
    )
    assertDataFrameEqual(actual, expected)


def test_input_should_read_table_at_version_zero(spark: SparkSession):
    """
    Version 0 is the first version of the table, not a missing version.
    """
    # Arrange
    target_table = "spark_catalog.default.table_input_at_version_zero"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            ('lorem', 1)
        AS t(word, count)
        """
    )
    spark.sql(f"INSERT INTO {target_table} VALUES ('ipsum', 2)")

    # Act
    result = SparkTableInput(
        name="test",
        table=target_table,
        version=0,
    ).read()

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            ("lorem", 1),
        ],
        schema="word STRING, count INT",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-01-15 12:00:00",
        date(2026, 1, 15),
        datetime(2026, 1, 15, 12, 0, 0),
    ],
)
def test_input_should_read_table_at_timestamp(
    spark: SparkSession, timestamp: str | date | datetime
):
    """
    Accepts strings, dates and datetimes, since YAML loads unquoted timestamps
    as dates or datetimes.

    Delta resolves time travel by the modification time of its commit files, so
    the commits are moved to 2026-01-01 and 2026-02-01 to place the timestamp
    between them.
    """
    # Arrange
    target_table = "spark_catalog.default.table_input_at_timestamp"
    spark.sql(f"DROP TABLE IF EXISTS {target_table}")
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            ('lorem', 1)
        AS t(word, count)
        """
    )
    spark.sql(f"INSERT INTO {target_table} VALUES ('ipsum', 2)")
    location = spark.sql(f"DESCRIBE DETAIL {target_table}").first()["location"]
    delta_log = Path(urlparse(location).path) / "_delta_log"
    first_commit_time = datetime(2026, 1, 1, tzinfo=UTC).timestamp()
    second_commit_time = datetime(2026, 2, 1, tzinfo=UTC).timestamp()
    os.utime(delta_log / "00000000000000000000.json", (first_commit_time, first_commit_time))
    os.utime(delta_log / "00000000000000000001.json", (second_commit_time, second_commit_time))

    # Act
    result = SparkTableInput(
        name="test",
        table=target_table,
        timestamp=timestamp,
    ).read()

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            ("lorem", 1),
        ],
        schema="word STRING, count INT",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# Testing SparkTableInput - Lineage
# ============================================================================


def test_external_datasets_should_return_table_as_catalog_input():
    # Arrange
    target_table = "iceberg.default.sales"
    step = SparkTableInput(
        name="test",
        table=target_table,
    )

    # Act
    result = step.external_datasets()

    # Assert
    actual = [(d.tiozin_namespace, d.tiozin_name) for d in result.inputs]
    expected = [("iceberg", "default.sales")]
    assert actual == expected


def test_external_datasets_should_return_query_tables_as_catalog_inputs():
    # Arrange
    sales_table = "iceberg.default.sales"
    customers_table = "spark_catalog.crm.customers"
    step = SparkTableInput(
        name="test",
        query=f"""
            SELECT s.order_id, s.amount, c.segment
            FROM {sales_table} s
            JOIN {customers_table} c USING (customer_id)
        """,
    )

    # Act
    result = step.external_datasets()

    # Assert
    actual = sorted((d.tiozin_namespace, d.tiozin_name) for d in result.inputs)
    expected = [
        ("iceberg", "default.sales"),
        ("spark_catalog", "crm.customers"),
    ]
    assert actual == expected


# ============================================================================
# Testing SparkTableInput - Errors
# ============================================================================


@pytest.mark.parametrize("source", [None, ""])
def test_input_should_raise_input_error_when_table_and_query_are_missing(source: str):
    # Act / Assert
    with pytest.raises(TiozinInputError):
        SparkTableInput(
            name="test",
            table=source,
            query=source,
        )


def test_input_should_raise_input_error_when_table_and_query_are_provided():
    # Arrange
    target_table = "spark_catalog.default.sales"

    # Act / Assert
    with pytest.raises(TiozinInputError):
        SparkTableInput(
            name="test",
            table=target_table,
            query=f"SELECT * FROM {target_table}",
        )


@pytest.mark.parametrize("version", [0, 1])
def test_input_should_raise_input_error_when_version_and_timestamp_are_provided(version: int):
    # Arrange
    target_table = "spark_catalog.default.sales"

    # Act / Assert
    with pytest.raises(TiozinInputError):
        SparkTableInput(
            name="test",
            table=target_table,
            version=version,
            timestamp="2026-01-15 12:00:00",
        )


@pytest.mark.parametrize(
    ("version", "timestamp"),
    [
        (0, None),
        (1, None),
        (None, "2026-01-15 12:00:00"),
    ],
)
def test_input_should_raise_input_error_when_query_has_time_travel(version: int, timestamp: str):
    # Arrange
    target_table = "spark_catalog.default.sales"

    # Act / Assert
    with pytest.raises(TiozinInputError):
        SparkTableInput(
            name="test",
            query=f"SELECT * FROM {target_table}",
            version=version,
            timestamp=timestamp,
        )
