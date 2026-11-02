import pytest
from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin.family.tio_spark.functions import merge_into

# ============================================================================
# merge_into
# ============================================================================


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_merge_into_should_merge_rows_by_key(spark: SparkSession, catalog: str, table_format: str):
    """Updates the rows that match the key and inserts the others."""
    # Arrange
    target_table = f"{catalog}.default.functions_merged"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            (1, 'original@example.com'),
            (2, 'original@example.com')
        AS t(id, email)
        """
    )
    merge_data = spark.createDataFrame(
        [
            (2, "updated@example.com"),
            (3, "inserted@example.com"),
        ],
        schema="id INT, email STRING",
    )

    # Act
    merge_into(merge_data, target_table, ["id"])

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "original@example.com"),
            (2, "updated@example.com"),
            (3, "inserted@example.com"),
        ],
        schema="id INT, email STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_merge_into_should_merge_rows_by_all_keys(spark: SparkSession):
    """Matches a row only when every key matches."""
    # Arrange
    target_table = "iceberg.default.functions_merged_by_keys"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING iceberg
        AS SELECT * FROM VALUES
            ('BR', 1, 'old'),
            ('US', 1, 'kept')
        AS t(region, id, name)
        """
    )
    merge_data = spark.createDataFrame(
        [
            ("BR", 1, "new"),
        ],
        schema="region STRING, id INT, name STRING",
    )

    # Act
    merge_into(merge_data, target_table, ["region", "id"])

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            ("BR", 1, "new"),
            ("US", 1, "kept"),
        ],
        schema="region STRING, id INT, name STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_merge_into_should_merge_rows_when_key_needs_quoting(
    spark: SparkSession, catalog: str, table_format: str
):
    """Matches rows by a key whose column name needs quoting."""
    # Arrange
    target_table = f"{catalog}.default.functions_merged_by_quoted_key"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            (1, 'original@example.com'),
            (2, 'original@example.com')
        AS t(`customer-id`, email)
        """
    )
    merge_data = spark.createDataFrame(
        [
            (2, "updated@example.com"),
            (3, "inserted@example.com"),
        ],
        schema="`customer-id` INT, email STRING",
    )

    # Act
    merge_into(merge_data, target_table, ["customer-id"])

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "original@example.com"),
            (2, "updated@example.com"),
            (3, "inserted@example.com"),
        ],
        schema="`customer-id` INT, email STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_merge_into_should_preserve_excluded_column(
    spark: SparkSession, catalog: str, table_format: str
):
    """Keeps the table value of an excluded column, even NULL, on matched rows only."""
    # Arrange
    target_table = f"{catalog}.default.functions_merged_excluded_column"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            (1, 'original@example.com', '2025-01-01'),
            (2, 'original@example.com', '2025-01-02'),
            (3, 'original@example.com', CAST(NULL AS STRING))
        AS t(id, email, created_at)
        """
    )
    merge_data = spark.createDataFrame(
        [
            (2, "updated@example.com", "2026-06-01"),
            (3, "updated@example.com", "2026-06-01"),
            (4, "inserted@example.com", "2026-06-01"),
        ],
        schema="id INT, email STRING, created_at STRING",
    )

    # Act
    merge_into(merge_data, target_table, ["id"], ["created_at"])

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "original@example.com", "2025-01-01"),
            (2, "updated@example.com", "2025-01-02"),
            (3, "updated@example.com", None),
            (4, "inserted@example.com", "2026-06-01"),
        ],
        schema="id INT, email STRING, created_at STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_merge_into_should_preserve_excluded_struct_column(
    spark: SparkSession, catalog: str, table_format: str
):
    """Keeps every field of an excluded struct column on matched rows."""
    # Arrange
    target_table = f"{catalog}.default.functions_merged_excluded_struct"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            (1, 'original@example.com', named_struct('created_at', '2025-01-01', 'source', 'crm'))
        AS t(id, email, audit)
        """
    )
    merge_data = spark.createDataFrame(
        [
            (1, "updated@example.com", ("2026-06-01", "web")),
            (2, "inserted@example.com", ("2026-06-01", "web")),
        ],
        schema="id INT, email STRING, audit STRUCT<created_at: STRING, source: STRING>",
    )

    # Act
    merge_into(merge_data, target_table, ["id"], ["audit"])

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "updated@example.com", ("2025-01-01", "crm")),
            (2, "inserted@example.com", ("2026-06-01", "web")),
        ],
        schema="id INT, email STRING, audit STRUCT<created_at: STRING, source: STRING>",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)
