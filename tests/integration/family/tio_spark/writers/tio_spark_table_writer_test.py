from datetime import date

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as sf
from pyspark.testing import assertDataFrameEqual, assertSchemaEqual

from tiozin.exceptions import RequiredArgumentError, TiozinInputError
from tiozin.family.tio_spark.writers.table_writer import TioSparkSimpleTableWriter

# ============================================================================
# Testing TioSparkSimpleTableWriter - Generic
# ============================================================================


@pytest.mark.parametrize(
    "mode",
    ["append", "overwrite", "drop_overwrite", "truncate", "overwrite_partitions", "merge"],
)
def test_save_should_create_table_when_table_is_missing(spark: SparkSession, mode: str):
    """Creates a missing table with the DataFrame rows, whatever the mode."""
    # Arrange
    target_table = f"iceberg.default.writer_created_by_{mode}"
    initial_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=initial_data,
        table=target_table,
    ).mode(mode).onMergeInto(keys="id").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize(
    "catalog, table_format, provider",
    [
        ("spark_catalog", "delta", "delta"),
        ("iceberg", "iceberg", "iceberg"),
    ],
)
def test_save_should_create_table_with_format(
    spark: SparkSession, catalog: str, table_format: str, provider: str
):
    """Creates the table with the given format."""
    # Arrange
    target_table = f"{catalog}.default.writer_formatted_as_{table_format}"
    initial_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=initial_data,
        table=target_table,
    ).format(table_format).save()

    # Assert
    actual = (
        spark.sql(f"DESCRIBE TABLE EXTENDED {target_table}")
        .where("col_name = 'Provider'")
        .first()["data_type"]
    )
    expected = provider
    assert actual == expected


def test_save_should_create_table_with_table_property(spark: SparkSession):
    """Creates the table with the given table property."""
    # Arrange
    target_table = "iceberg.default.writer_with_table_property"
    initial_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=initial_data,
        table=target_table,
    ).tableProperty("tiozin.layer", "gold").save()

    # Assert
    actual = spark.sql(f"SHOW TBLPROPERTIES {target_table} ('tiozin.layer')")
    expected = spark.createDataFrame(
        [
            ("tiozin.layer", "gold"),
        ],
        schema="key STRING, value STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_save_should_create_table_with_table_properties(spark: SparkSession):
    """Creates the table with several given table properties."""
    # Arrange
    target_table = "iceberg.default.writer_with_table_properties"
    initial_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=initial_data,
        table=target_table,
    ).tableProperties(
        **{
            "tiozin.layer": "gold",
            "tiozin.owner": "data-team",
        }
    ).save()

    # Assert
    actual = spark.sql(f"SHOW TBLPROPERTIES {target_table}").where("key LIKE 'tiozin.%'")
    expected = spark.createDataFrame(
        [
            ("tiozin.layer", "gold"),
            ("tiozin.owner", "data-team"),
        ],
        schema="key STRING, value STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_save_should_create_table_partitioned_by_columns(spark: SparkSession):
    """Creates the table partitioned by the given columns."""
    # Arrange
    target_table = "iceberg.default.writer_partitioned"
    initial_data = spark.createDataFrame(
        [
            (1, "BR"),
            (2, "US"),
        ],
        schema="id INT, region STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=initial_data,
        table=target_table,
    ).partitionedBy(sf.col("region")).save()

    # Assert
    actual = spark.sql(f"SELECT partition.region FROM {target_table}.partitions")
    expected = spark.createDataFrame(
        [
            ("BR",),
            ("US",),
        ],
        schema="region STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_save_should_create_table_partitioned_by_column_name(spark: SparkSession):
    """Creates the table partitioned by a column given by name."""
    # Arrange
    target_table = "iceberg.default.writer_partitioned_by_name"
    initial_data = spark.createDataFrame(
        [
            (1, "BR"),
            (2, "US"),
        ],
        schema="id INT, region STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=initial_data,
        table=target_table,
    ).partitionedBy("region").save()

    # Assert
    actual = spark.sql(f"SELECT partition.region FROM {target_table}.partitions")
    expected = spark.createDataFrame(
        [
            ("BR",),
            ("US",),
        ],
        schema="region STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize(
    "transform, expression",
    [
        ("days", "days(created_at)"),
        ("bucket", "bucket(16, id)"),
    ],
)
def test_save_should_create_table_partitioned_by_transform(
    spark: SparkSession, transform: str, expression: str
):
    """Creates the table partitioned by a transform given as an expression."""
    # Arrange
    target_table = f"iceberg.default.writer_partitioned_by_{transform}"
    initial_data = spark.createDataFrame(
        [
            (1, date(2026, 1, 15)),
        ],
        schema="id INT, created_at DATE",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=initial_data,
        table=target_table,
    ).partitionedBy(expression).save()

    # Assert
    actual = spark.sql(f"DESCRIBE TABLE {target_table}").where("col_name = 'Part 0'")
    expected = spark.createDataFrame(
        [
            ("Part 0", expression, ""),
        ],
        schema="col_name STRING, data_type STRING, comment STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_save_should_apply_write_option(spark: SparkSession):
    """Applies a write option, observed as a custom Iceberg snapshot property."""
    # Arrange
    target_table = "iceberg.default.writer_with_option"
    spark.sql(f"CREATE TABLE {target_table} (id INT, name STRING) USING iceberg")
    input_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).option("snapshot-property.tiozin.run", "run-1").save()

    # Assert
    actual = spark.sql(f"SELECT summary['tiozin.run'] AS run FROM {target_table}.snapshots")
    expected = spark.createDataFrame(
        [
            ("run-1",),
        ],
        schema="run STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_save_should_apply_write_options(spark: SparkSession):
    """Applies several write options, observed as custom Iceberg snapshot properties."""
    # Arrange
    target_table = "iceberg.default.writer_with_options"
    spark.sql(f"CREATE TABLE {target_table} (id INT, name STRING) USING iceberg")
    input_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).options(
        **{
            "snapshot-property.tiozin.run": "run-1",
            "snapshot-property.tiozin.step": "step-1",
        }
    ).save()

    # Assert
    actual = spark.sql(
        f"SELECT summary['tiozin.run'] AS run, summary['tiozin.step'] AS step "
        f"FROM {target_table}.snapshots"
    )
    expected = spark.createDataFrame(
        [
            ("run-1", "step-1"),
        ],
        schema="run STRING, step STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_mode_should_raise_input_error_when_mode_is_unsupported(spark: SparkSession):
    # Arrange
    target_table = "iceberg.default.writer_unsupported_mode"
    input_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )
    writer = TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    )

    # Act / Assert
    with pytest.raises(TiozinInputError):
        writer.mode("upsert")


def test_save_should_raise_input_error_when_partition_expression_is_invalid(spark: SparkSession):
    # Arrange
    target_table = "iceberg.default.writer_invalid_partition_expression"
    input_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )
    writer = TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).partitionedBy("days()")

    # Act
    with pytest.raises(TiozinInputError) as exc_info:
        writer.save()

    # Assert
    actual = str(exc_info.value)
    expected = "Invalid partition expression: 'days()'"
    assert actual == expected


def test_save_should_keep_table_schema_when_partition_expression_is_invalid(spark: SparkSession):
    """Fails before schema evolution changes the existing table."""
    # Arrange
    target_table = "iceberg.default.writer_invalid_partition_keeps_schema"
    spark.sql(f"CREATE TABLE {target_table} (id INT, name STRING) USING iceberg")
    input_data = spark.createDataFrame(
        [
            (1, "hello", "new@example.com"),
        ],
        schema="id INT, name STRING, email STRING",
    )
    writer = (
        TioSparkSimpleTableWriter(
            df=input_data,
            table=target_table,
        )
        .withSchemaEvolution()
        .partitionedBy("days()")
    )

    # Act
    with pytest.raises(TiozinInputError):
        writer.save()

    # Assert
    actual = spark.table(target_table).schema
    expected = spark.createDataFrame([], schema="id INT, name STRING").schema
    assertSchemaEqual(actual, expected)


# ============================================================================
# Testing TioSparkSimpleTableWriter - Append
# ============================================================================


def test_save_should_append_rows_by_default(spark: SparkSession):
    """Adds rows to an existing table when no mode is set."""
    # Arrange
    target_table = "iceberg.default.writer_appended_by_default"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING iceberg
        AS SELECT * FROM VALUES
            (1, 'old')
        AS t(id, name)
        """
    )
    input_data = spark.createDataFrame(
        [
            (2, "new"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "old"),
            (2, "new"),
        ],
        schema="id INT, name STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_append_rows(spark: SparkSession, catalog: str, table_format: str):
    """Adds rows to an existing table in the `append` mode."""
    # Arrange
    target_table = f"{catalog}.default.writer_appended"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            (1, 'old')
        AS t(id, name)
        """
    )
    input_data = spark.createDataFrame(
        [
            (2, "new"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).format(table_format).mode("append").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "old"),
            (2, "new"),
        ],
        schema="id INT, name STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_evolve_schema_when_mode_is_append(
    spark: SparkSession, catalog: str, table_format: str
):
    """Adds a new column in the `append` mode, and kept rows get NULL."""
    # Arrange
    target_table = f"{catalog}.default.writer_evolved_column_append"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        PARTITIONED BY (region)
        AS SELECT * FROM VALUES
            (1, 'BR'),
            (2, 'US')
        AS t(id, region)
        """
    )
    input_data = spark.createDataFrame(
        [
            (3, "JP", "new@example.com"),
        ],
        schema="id INT, region STRING, email STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).format(table_format).withSchemaEvolution().mode("append").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "BR", None),
            (2, "US", None),
            (3, "JP", "new@example.com"),
        ],
        schema="id INT, region STRING, email STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


# ============================================================================
# Testing TioSparkSimpleTableWriter - Overwrite
# ============================================================================


@pytest.mark.usefixtures("skip_delta_replace_bug")
@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_recreate_table_when_mode_is_overwrite(
    spark: SparkSession, catalog: str, table_format: str
):
    """Replaces the schema and rows of an existing table in the `overwrite` mode."""
    # Arrange
    target_table = f"{catalog}.default.writer_overwritten"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            (1, 'old')
        AS t(id, name)
        """
    )
    replacement_data = spark.createDataFrame(
        [
            (2, "new@example.com"),
        ],
        schema="id INT, email STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=replacement_data,
        table=target_table,
    ).format(table_format).mode("overwrite").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (2, "new@example.com"),
        ],
        schema="id INT, email STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.usefixtures("skip_delta_replace_bug")
@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_add_new_column_when_mode_is_overwrite(
    spark: SparkSession, catalog: str, table_format: str
):
    """Adds a new column in the `overwrite` mode, and no previous row is kept."""
    # Arrange
    target_table = f"{catalog}.default.writer_evolved_column_overwrite"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        PARTITIONED BY (region)
        AS SELECT * FROM VALUES
            (1, 'BR'),
            (2, 'US')
        AS t(id, region)
        """
    )
    input_data = spark.createDataFrame(
        [
            (3, "JP", "new@example.com"),
        ],
        schema="id INT, region STRING, email STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).format(table_format).mode("overwrite").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (3, "JP", "new@example.com"),
        ],
        schema="id INT, region STRING, email STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.usefixtures("skip_delta_replace_bug")
@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_change_column_type_when_mode_is_overwrite(
    spark: SparkSession, catalog: str, table_format: str
):
    """Replaces the type of an existing column in the `overwrite` mode."""
    # Arrange
    target_table = f"{catalog}.default.writer_overwritten_column_type"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            ('1', 'old')
        AS t(id, name)
        """
    )
    replacement_data = spark.createDataFrame(
        [
            (2, "new"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=replacement_data,
        table=target_table,
    ).format(table_format).mode("overwrite").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (2, "new"),
        ],
        schema="id INT, name STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


# ============================================================================
# Testing TioSparkSimpleTableWriter - Drop Overwrite
# ============================================================================


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_recreate_table_when_mode_is_drop_overwrite(
    spark: SparkSession, catalog: str, table_format: str
):
    """Replaces the schema and rows of an existing table in the `drop_overwrite` mode."""
    # Arrange
    target_table = f"{catalog}.default.writer_drop_overwritten"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            (1, 'old')
        AS t(id, name)
        """
    )
    replacement_data = spark.createDataFrame(
        [
            (2, "new@example.com"),
        ],
        schema="id INT, email STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=replacement_data,
        table=target_table,
    ).format(table_format).mode("drop_overwrite").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (2, "new@example.com"),
        ],
        schema="id INT, email STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_save_should_restart_delta_history_when_mode_is_drop_overwrite(spark: SparkSession):
    """Keeps only the new table's version in the Delta history in the `drop_overwrite` mode."""
    # Arrange
    target_table = "spark_catalog.default.writer_drop_overwritten_history"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING delta
        AS SELECT * FROM VALUES
            (1, 'old')
        AS t(id, name)
        """
    )
    replacement_data = spark.createDataFrame(
        [
            (2, "new"),
        ],
        schema="id INT, name STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=replacement_data,
        table=target_table,
    ).format("delta").mode("drop_overwrite").save()

    # Assert
    actual = [row["version"] for row in spark.sql(f"DESCRIBE HISTORY {target_table}").collect()]
    expected = [0]
    assert actual == expected


# ============================================================================
# Testing TioSparkSimpleTableWriter - Truncate
# ============================================================================


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_replace_all_rows_when_mode_is_truncate(
    spark: SparkSession, catalog: str, table_format: str
):
    """Replaces every row of an existing table in the `truncate` mode."""
    # Arrange
    target_table = f"{catalog}.default.writer_truncated"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            (1, 'BR'),
            (2, 'US')
        AS t(id, region)
        """
    )
    replacement_data = spark.createDataFrame(
        [
            (3, "BR"),
        ],
        schema="id INT, region STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=replacement_data,
        table=target_table,
    ).format(table_format).mode("truncate").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (3, "BR"),
        ],
        schema="id INT, region STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_evolve_schema_when_mode_is_truncate(
    spark: SparkSession, catalog: str, table_format: str
):
    """Adds a new column in the `truncate` mode, and no previous row is kept."""
    # Arrange
    target_table = f"{catalog}.default.writer_evolved_column_truncate"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        PARTITIONED BY (region)
        AS SELECT * FROM VALUES
            (1, 'BR'),
            (2, 'US')
        AS t(id, region)
        """
    )
    input_data = spark.createDataFrame(
        [
            (3, "JP", "new@example.com"),
        ],
        schema="id INT, region STRING, email STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).format(table_format).withSchemaEvolution().mode("truncate").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (3, "JP", "new@example.com"),
        ],
        schema="id INT, region STRING, email STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


# ============================================================================
# Testing TioSparkSimpleTableWriter - Overwrite Partitions
# ============================================================================


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_overwrite_partitions_present_in_dataframe(
    spark: SparkSession, catalog: str, table_format: str
):
    """Replaces only the partitions present in the DataFrame in the `overwrite_partitions` mode."""
    # Arrange
    target_table = f"{catalog}.default.writer_overwritten_partitions"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        PARTITIONED BY (region)
        AS SELECT * FROM VALUES
            (1, 'BR'),
            (2, 'US')
        AS t(id, region)
        """
    )
    replacement_data = spark.createDataFrame(
        [
            (3, "BR"),
        ],
        schema="id INT, region STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=replacement_data,
        table=target_table,
    ).format(table_format).mode("overwrite_partitions").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (2, "US"),
            (3, "BR"),
        ],
        schema="id INT, region STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_evolve_schema_when_mode_is_overwrite_partitions(
    spark: SparkSession, catalog: str, table_format: str
):
    """Adds a new column in the `overwrite_partitions` mode, and kept rows get NULL."""
    # Arrange
    target_table = f"{catalog}.default.writer_evolved_column_overwrite_partitions"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        PARTITIONED BY (region)
        AS SELECT * FROM VALUES
            (1, 'BR'),
            (2, 'US')
        AS t(id, region)
        """
    )
    input_data = spark.createDataFrame(
        [
            (3, "JP", "new@example.com"),
        ],
        schema="id INT, region STRING, email STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).format(table_format).withSchemaEvolution().mode("overwrite_partitions").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "BR", None),
            (2, "US", None),
            (3, "JP", "new@example.com"),
        ],
        schema="id INT, region STRING, email STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


# ============================================================================
# Testing TioSparkSimpleTableWriter - Merge
# ============================================================================


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_merge_rows(spark: SparkSession, catalog: str, table_format: str):
    """Updates matched rows, except excluded columns, and inserts the others."""
    # Arrange
    target_table = f"{catalog}.default.writer_merged"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        AS SELECT * FROM VALUES
            (1, 'original@example.com', '2025-01-01')
        AS t(id, email, created_at)
        """
    )
    merge_data = spark.createDataFrame(
        [
            (1, "updated@example.com", "2026-06-01"),
            (2, "inserted@example.com", "2026-06-01"),
        ],
        schema="id INT, email STRING, created_at STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=merge_data,
        table=target_table,
    ).format(table_format).mode("merge").onMergeInto(
        keys="id",
        exclude_fields="created_at",
    ).save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "updated@example.com", "2025-01-01"),
            (2, "inserted@example.com", "2026-06-01"),
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
def test_save_should_evolve_schema_when_mode_is_merge(
    spark: SparkSession, catalog: str, table_format: str
):
    """Adds a new column in the `merge` mode, and kept rows get NULL."""
    # Arrange
    target_table = f"{catalog}.default.writer_evolved_column_merge"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING {table_format}
        PARTITIONED BY (region)
        AS SELECT * FROM VALUES
            (1, 'BR'),
            (2, 'US')
        AS t(id, region)
        """
    )
    input_data = spark.createDataFrame(
        [
            (3, "JP", "new@example.com"),
        ],
        schema="id INT, region STRING, email STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).format(table_format).withSchemaEvolution().mode("merge").onMergeInto(keys="id").save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "BR", None),
            (2, "US", None),
            (3, "JP", "new@example.com"),
        ],
        schema="id INT, region STRING, email STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
@pytest.mark.parametrize(
    "mode",
    ["append", "truncate", "overwrite_partitions", "drop_overwrite"],
)
def test_save_should_ignore_merge_exclude_fields_when_mode_is_not_merge(
    spark: SparkSession, catalog: str, table_format: str, mode: str
):
    """Writes excluded columns and accepts unknown names outside the `merge` mode."""
    # Arrange
    target_table = f"{catalog}.default.writer_ignored_exclude_fields_{mode}"
    spark.sql(f"CREATE TABLE {target_table} (id INT, email STRING) USING {table_format}")
    input_data = spark.createDataFrame(
        [
            (1, "new@example.com"),
        ],
        schema="id INT, email STRING",
    )

    # Act
    TioSparkSimpleTableWriter(
        df=input_data,
        table=target_table,
    ).format(table_format).mode(mode).onMergeInto(
        exclude_fields=["email", "unknown"],
    ).save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            (1, "new@example.com"),
        ],
        schema="id INT, email STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


@pytest.mark.parametrize("merge_keys", [None, []])
def test_save_should_raise_required_argument_error_when_merge_keys_are_missing(
    spark: SparkSession, merge_keys: list[str]
):
    # Arrange
    target_table = "iceberg.default.writer_merge_without_keys"
    merge_data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )
    writer = (
        TioSparkSimpleTableWriter(
            df=merge_data,
            table=target_table,
        )
        .mode("merge")
        .onMergeInto(keys=merge_keys)
    )

    # Act / Assert
    with pytest.raises(RequiredArgumentError):
        writer.save()


@pytest.mark.parametrize(
    "merge_exclude_fields",
    ["unknown", "audit.created_at", ["email", "unknown"]],
)
def test_save_should_raise_input_error_when_merge_exclude_field_is_not_top_level_column(
    spark: SparkSession, merge_exclude_fields: str | list[str]
):
    # Arrange
    target_table = "iceberg.default.writer_merge_with_invalid_exclude_field"
    merge_data = spark.createDataFrame(
        [
            (1, "hello@example.com", ("2026-06-01",)),
        ],
        schema="id INT, email STRING, audit STRUCT<created_at: STRING>",
    )
    writer = (
        TioSparkSimpleTableWriter(
            df=merge_data,
            table=target_table,
        )
        .mode("merge")
        .onMergeInto(keys="id", exclude_fields=merge_exclude_fields)
    )

    # Act / Assert
    with pytest.raises(TiozinInputError):
        writer.save()


# ============================================================================
# Testing TioSparkSimpleTableWriter - Metrics
# ============================================================================


@pytest.mark.parametrize(
    "catalog,table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_metrics_should_report_saved_write(spark: SparkSession, catalog: str, table_format: str):
    """Reports the table, mode and format of the writer with the metrics of its write."""
    # Arrange
    target_table = f"{catalog}.default.writer_metrics_saved_write"
    new_data = spark.createDataFrame(
        [
            (1, "new"),
            (2, "new"),
        ],
        schema="id INT, name STRING",
    )
    writer = TioSparkSimpleTableWriter(
        df=new_data,
        table=target_table,
    ).format(table_format)
    writer.save()

    # Act
    result = writer.metrics()

    # Assert
    actual = (
        result.dataset,
        result.mode,
        result.format,
        result.rows_written,
    )
    expected = (
        f"{catalog}.default.writer_metrics_saved_write",
        "append",
        table_format,
        2,
    )
    assert actual == expected


def test_metrics_should_report_configured_mode(spark: SparkSession):
    # Arrange
    target_table = "iceberg.default.writer_metrics_configured_mode"
    spark.sql(f"CREATE TABLE {target_table} (id INT, name STRING) USING iceberg")
    new_data = spark.createDataFrame(
        [
            (1, "new"),
        ],
        schema="id INT, name STRING",
    )
    writer = (
        TioSparkSimpleTableWriter(
            df=new_data,
            table=target_table,
        )
        .format("iceberg")
        .mode("merge")
        .onMergeInto(keys="id")
    )
    writer.save()

    # Act
    result = writer.metrics()

    # Assert
    actual = result.mode
    expected = "merge"
    assert actual == expected


@pytest.mark.parametrize(
    "catalog,table_format,expected_format",
    [
        ("spark_catalog", "DELTA", "delta"),
        ("iceberg", "ICEBERG", "iceberg"),
    ],
)
def test_metrics_should_accept_case_insensitive_format(
    spark: SparkSession, catalog: str, table_format: str, expected_format: str
):
    # Arrange
    target_table = f"{catalog}.default.writer_metrics_upper_format"
    data = spark.createDataFrame(
        [
            (1, "hello"),
        ],
        schema="id INT, name STRING",
    )
    writer = TioSparkSimpleTableWriter(
        df=data,
        table=target_table,
    ).format(table_format)
    writer.save()

    # Act
    result = writer.metrics()

    # Assert
    actual = (
        result.format,
        result.rows_written,
    )
    expected = (expected_format, 1)
    assert actual == expected
