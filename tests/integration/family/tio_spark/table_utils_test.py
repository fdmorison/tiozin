from unittest.mock import MagicMock, patch

import pytest
from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin import OutputMetrics
from tiozin.exceptions import TiozinInputError
from tiozin.family.tio_spark.table_utils import evolve_schema, output_metrics


# ============================================================================
# Testing output_metrics - Iceberg
# ============================================================================
def test_output_metrics_should_report_iceberg_write(spark: SparkSession):
    """Reports the rows and bytes of the latest write and of the table after it."""
    # Arrange
    target_table = "iceberg.default.utils_metrics_iceberg"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING iceberg
        AS SELECT * FROM VALUES
            (1, 'existing')
        AS t(id, name)
        """
    )
    spark.sql(f"INSERT INTO {target_table} VALUES (2, 'new'), (3, 'new')")

    # Act
    result = output_metrics(spark, "iceberg", target_table, "append")

    # Assert
    actual = (
        result.dataset,
        result.mode,
        result.format,
        result.rows_written,
        result.rows_total,
        result.bytes_written > 0,
        result.bytes_total > result.bytes_written,
    )
    expected = (
        "iceberg.default.utils_metrics_iceberg",
        "append",
        "iceberg",
        2,
        3,
        True,
        True,
    )
    assert actual == expected


def test_output_metrics_should_report_iceberg_merge(spark: SparkSession):
    # Arrange
    target_table = "iceberg.default.utils_metrics_iceberg_merge"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING iceberg
        AS SELECT * FROM VALUES
            (1, 'old')
        AS t(id, name)
        """
    )
    spark.sql(
        f"""
        MERGE INTO {target_table} AS target
        USING (SELECT * FROM VALUES (1, 'updated'), (2, 'inserted') AS t(id, name)) AS source
        ON target.id = source.id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    )

    # Act
    result = output_metrics(spark, "iceberg", target_table, "merge")

    # Assert
    actual = (
        result.rows_written,
        result.rows_total,
        result.bytes_written > 0,
        result.bytes_total > 0,
    )
    expected = (2, 2, True, True)
    assert actual == expected


# ============================================================================
# Testing output_metrics - Delta
# ============================================================================
def test_output_metrics_should_report_delta_write(spark: SparkSession):
    """Reports no table row count, since Delta does not record it."""
    # Arrange
    target_table = "spark_catalog.default.utils_metrics_delta"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            (1, 'existing')
        AS t(id, name)
        """
    )
    spark.sql(f"INSERT INTO {target_table} VALUES (2, 'new'), (3, 'new')")

    # Act
    result = output_metrics(spark, "delta", target_table, "append")

    # Assert
    actual = (
        result.dataset,
        result.mode,
        result.format,
        result.rows_written,
        result.rows_total,
        result.bytes_written > 0,
        result.bytes_total > 0,
    )
    expected = (
        "spark_catalog.default.utils_metrics_delta",
        "append",
        "delta",
        2,
        None,
        True,
        True,
    )
    assert actual == expected


def test_output_metrics_should_report_delta_merge(spark: SparkSession):
    """Reports the merge metrics, which Delta records under different keys than a write."""
    # Arrange
    target_table = "spark_catalog.default.utils_metrics_delta_merge"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            (1, 'old')
        AS t(id, name)
        """
    )
    spark.sql(
        f"""
        MERGE INTO {target_table} AS target
        USING (SELECT * FROM VALUES (1, 'updated'), (2, 'inserted') AS t(id, name)) AS source
        ON target.id = source.id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    )

    # Act
    result = output_metrics(spark, "delta", target_table, "merge")

    # Assert
    actual = (
        result.rows_written,
        result.rows_total,
        result.bytes_written > 0,
        result.bytes_total > 0,
    )
    expected = (2, None, True, True)
    assert actual == expected


@pytest.mark.parametrize(
    "catalog,table_format,expected_format",
    [
        ("spark_catalog", "DELTA", "delta"),
        ("iceberg", "ICEBERG", "iceberg"),
    ],
)
def test_output_metrics_should_accept_case_insensitive_format(
    spark: SparkSession, catalog: str, table_format: str, expected_format: str
):
    """Reads the metrics of the format and reports its lowercased name."""
    # Arrange
    target_table = f"{catalog}.default.utils_metrics_upper_format"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {expected_format}
        AS SELECT * FROM VALUES
            (1, 'hello')
        AS t(id, name)
        """
    )

    # Act
    result = output_metrics(spark, table_format, target_table, "append")

    # Assert
    actual = (
        result.format,
        result.rows_written,
    )
    expected = (expected_format, 1)
    assert actual == expected


# ============================================================================
# Testing output_metrics - Zero metrics
# ============================================================================
@pytest.mark.parametrize(
    "catalog,table_format,rows_total,no_bytes_written",
    [
        ("spark_catalog", "delta", None, False),
        ("iceberg", "iceberg", 0, True),
    ],
)
def test_output_metrics_should_report_zero_when_writing_nothing_to_empty_table(
    spark: SparkSession,
    catalog: str,
    table_format: str,
    rows_total: int | None,
    no_bytes_written: bool,
):
    """Delta still adds an empty file, so its bytes written are not zero."""
    # Arrange
    target_table = f"{catalog}.default.utils_metrics_nothing_written"
    spark.createDataFrame(
        [],
        schema="id INT, name STRING",
    ).writeTo(target_table).using(table_format).create()

    # Act
    result = output_metrics(spark, table_format, target_table, "append")

    # Assert
    actual = (
        result.rows_written,
        result.rows_total,
        result.bytes_written == 0,
        result.bytes_total,
    )
    expected = (0, rows_total, no_bytes_written, 0)
    assert actual == expected


# ============================================================================
# Testing output_metrics - Unknown metrics
# ============================================================================
def test_output_metrics_should_return_no_metrics_when_format_is_unknown(spark: SparkSession):
    # Arrange
    target_table = "spark_catalog.default.utils_metrics_unknown_format"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING parquet
        AS SELECT * FROM VALUES
            (1, 'hello')
        AS t(id, name)
        """
    )

    # Act
    result = output_metrics(spark, "parquet", target_table, "append")

    # Assert
    actual = result
    expected = OutputMetrics(
        dataset="spark_catalog.default.utils_metrics_unknown_format",
        mode="append",
        format="parquet",
    )
    assert actual == expected


@pytest.mark.parametrize(
    "catalog,table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_output_metrics_should_return_no_metrics_when_table_does_not_exist(
    spark: SparkSession, catalog: str, table_format: str
):
    # Arrange
    target_table = f"{catalog}.default.utils_metrics_missing_table"

    # Act
    result = output_metrics(spark, table_format, target_table, "append")

    # Assert
    actual = (
        result.dataset,
        result.mode,
        result.format,
        result.rows_written,
        result.rows_total,
        result.bytes_written,
        result.bytes_total,
    )
    expected = (
        f"{catalog}.default.utils_metrics_missing_table",
        "append",
        table_format,
        None,
        None,
        None,
        None,
    )
    assert actual == expected


@patch("tiozin.family.tio_spark.table_utils.logger")
def test_output_metrics_should_log_warning_when_table_does_not_exist(
    logger: MagicMock, spark: SparkSession
):
    # Arrange
    target_table = "iceberg.default.utils_metrics_missing_table_warning"

    # Act
    output_metrics(spark, "iceberg", target_table, "append")

    # Assert
    assert (
        "Could not read the metrics of the write to "
        "iceberg.default.utils_metrics_missing_table_warning"
    ) in str(logger.warning.call_args)


# ============================================================================
# Testing evolve_schema
# ============================================================================
@pytest.mark.parametrize(
    "catalog,table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_evolve_schema_should_add_new_columns(spark: SparkSession, catalog: str, table_format: str):
    """Adds the column without writing the DataFrame, so kept rows get NULL."""
    # Arrange
    target_table = f"{catalog}.default.utils_evolved_column"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            (1)
        AS t(id)
        """
    )
    input_data = spark.createDataFrame(
        [
            (2, "new@example.com"),
        ],
        schema="id INT, email STRING",
    )

    # Act
    evolve_schema(input_data, target_table, table_format)

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, None),
        ],
        schema="id INT, email STRING",
    )
    assertDataFrameEqual(actual, expected)


def test_evolve_schema_should_accept_case_insensitive_format(spark: SparkSession):
    # Arrange
    target_table = "spark_catalog.default.utils_evolved_upper_format"
    spark.sql(f"CREATE TABLE {target_table} (id INT) USING delta")
    input_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    evolve_schema(input_data, target_table, "DELTA")

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [],
        schema="id INT, name STRING",
    )
    assertDataFrameEqual(actual, expected)


def test_evolve_schema_should_not_leave_temporary_property_on_iceberg_table(spark: SparkSession):
    """Leaves the table properties as they were before the schema evolution."""
    # Arrange
    target_table = "iceberg.default.utils_evolved_without_accept_any_schema"
    spark.sql(f"CREATE TABLE {target_table} (id INT) USING iceberg")
    input_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    evolve_schema(input_data, target_table, "iceberg")

    # Assert
    actual = (
        spark.sql(f"SHOW TBLPROPERTIES {target_table}")
        .filter("key = 'write.spark.accept-any-schema'")
        .collect()
    )
    expected = []
    assert actual == expected


def test_evolve_schema_should_preserve_previous_properties_on_iceberg_table(spark: SparkSession):
    """Keeps the property when the table already had it before the schema evolution."""
    # Arrange
    target_table = "iceberg.default.utils_evolved_with_accept_any_schema"
    spark.sql(
        f"""
        CREATE TABLE {target_table} (id INT) USING iceberg
        TBLPROPERTIES ('write.spark.accept-any-schema' = 'true')
        """
    )
    input_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    evolve_schema(input_data, target_table, "iceberg")

    # Assert
    actual = [
        row["value"]
        for row in spark.sql(f"SHOW TBLPROPERTIES {target_table}")
        .filter("key = 'write.spark.accept-any-schema'")
        .collect()
    ]
    expected = ["true"]
    assert actual == expected


def test_evolve_schema_should_not_change_delta_table_properties(spark: SparkSession):
    """Observes the Delta history, which records every change to the table properties."""
    # Arrange
    target_table = "spark_catalog.default.utils_evolved_without_properties"
    spark.sql(f"CREATE TABLE {target_table} (id INT) USING delta")
    input_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    evolve_schema(input_data, target_table, "delta")

    # Assert
    operations = [
        row["operation"] for row in spark.sql(f"DESCRIBE HISTORY {target_table}").collect()
    ]
    assert "SET TBLPROPERTIES" not in operations


@pytest.mark.parametrize(
    "input_schema",
    [
        "id INT, name STRING",
        "id INT, name STRING, email STRING",
    ],
)
def test_evolve_schema_should_raise_input_error_when_format_is_unsupported(
    spark: SparkSession, input_schema: str
):
    """Raises whether or not the DataFrame brings new columns."""
    # Arrange
    target_table = "spark_catalog.default.utils_evolved_unsupported_format"
    spark.sql(f"CREATE TABLE IF NOT EXISTS {target_table} (id INT, name STRING) USING parquet")
    input_data = spark.createDataFrame(
        [],
        schema=input_schema,
    )

    # Act / Assert
    with pytest.raises(TiozinInputError, match="parquet"):
        evolve_schema(input_data, target_table, "parquet")
