import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as sf
from pyspark.testing import assertDataFrameEqual

from tiozin.exceptions import RequiredArgumentError, TiozinInputError
from tiozin.family.tio_spark.writers.table_writer import TioSparkTableWriter

# ============================================================================
# Testing TioSparkTableWriter - Generic
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
    TioSparkTableWriter(
        df=initial_data,
        table=target_table,
    ).mode(mode, merge_keys="id").save()

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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
    writer = TioSparkTableWriter(
        df=input_data,
        table=target_table,
    )

    # Act / Assert
    with pytest.raises(TiozinInputError):
        writer.mode("upsert")


# ============================================================================
# Testing TioSparkTableWriter - Append
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
# Testing TioSparkTableWriter - Overwrite
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
# Testing TioSparkTableWriter - Drop Overwrite
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
        df=replacement_data,
        table=target_table,
    ).format("delta").mode("drop_overwrite").save()

    # Assert
    actual = [row["version"] for row in spark.sql(f"DESCRIBE HISTORY {target_table}").collect()]
    expected = [0]
    assert actual == expected


# ============================================================================
# Testing TioSparkTableWriter - Truncate
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
# Testing TioSparkTableWriter - Overwrite Partitions
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
    TioSparkTableWriter(
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
    TioSparkTableWriter(
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
# Testing TioSparkTableWriter - Merge
# ============================================================================


@pytest.mark.parametrize(
    "catalog, table_format",
    [
        ("spark_catalog", "delta"),
        ("iceberg", "iceberg"),
    ],
)
def test_save_should_merge_rows_by_key(spark: SparkSession, catalog: str, table_format: str):
    """Updates the rows that match the key and inserts the others in the `merge` mode."""
    # Arrange
    target_table = f"{catalog}.default.writer_merged"
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
    TioSparkTableWriter(
        df=merge_data,
        table=target_table,
    ).format(table_format).mode("merge", merge_keys="id").save()

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


def test_save_should_merge_rows_by_all_keys(spark: SparkSession):
    """Matches a row only when every key matches in the `merge` mode."""
    # Arrange
    target_table = "iceberg.default.writer_merged_by_keys"
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
    TioSparkTableWriter(
        df=merge_data,
        table=target_table,
    ).mode("merge", merge_keys=["region", "id"]).save()

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
    TioSparkTableWriter(
        df=input_data,
        table=target_table,
    ).format(table_format).withSchemaEvolution().mode("merge", merge_keys="id").save()

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


@pytest.mark.parametrize("merge_keys", [None, []])
def test_mode_should_raise_required_argument_error_when_merge_keys_are_missing(
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
    writer = TioSparkTableWriter(
        df=merge_data,
        table=target_table,
    )

    # Act / Assert
    with pytest.raises(RequiredArgumentError):
        writer.mode("merge", merge_keys=merge_keys)
