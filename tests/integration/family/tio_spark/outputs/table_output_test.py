import pytest
from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin.exceptions import TiozinInputError
from tiozin.family.tio_spark.outputs.table_output import SparkTableOutput

# ============================================================================
# Testing SparkTableOutput - Writing
# ============================================================================


def test_output_should_write_table(spark: SparkSession):
    """
    Happy path: the output does what it must do, write the data to the table.
    """
    # Arrange
    target_table = "iceberg.default.table_output_written"
    spark.sql(
        f"""
        CREATE TABLE {target_table} USING iceberg
        AS SELECT * FROM VALUES
            ('old', 0)
        AS t(word, count)
        """
    )
    input_data = spark.createDataFrame(
        [
            ("new", 1),
        ],
        schema="word STRING, count INT",
    )

    # Act
    SparkTableOutput(
        name="test",
        table=target_table,
    ).write(input_data).save()

    # Assert
    actual = spark.table(target_table)
    expected = spark.createDataFrame(
        [
            ("old", 0),
            ("new", 1),
        ],
        schema="word STRING, count INT",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_output_should_create_table(spark: SparkSession):
    """
    Ensures the output creates a missing table and that its integration with the
    writer works: every parameter reaches the writer and shapes the created table.
    """
    # Arrange
    target_table = "spark_catalog.default.table_output_created"
    input_data = spark.createDataFrame(
        [
            (1, "BR"),
            (2, "US"),
        ],
        schema="id INT, region STRING",
    )

    # Act
    SparkTableOutput(
        name="test",
        table=target_table,
        format="delta",
        mode="merge",
        keys="id",
        partition_by="region",
        properties={
            "tiozin.layer": "gold",
        },
    ).write(input_data).save()

    # Assert
    actual = spark.sql(f"DESCRIBE DETAIL {target_table}").select(
        "format",
        "partitionColumns",
        "properties",
    )
    expected = spark.createDataFrame(
        [
            ("delta", ["region"], {"tiozin.layer": "gold"}),
        ],
        schema="format STRING, partitionColumns ARRAY<STRING>, properties MAP<STRING, STRING>",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# Testing SparkTableOutput - Lineage
# ============================================================================


def test_external_datasets_should_return_table_as_catalog_output():
    # Arrange
    step = SparkTableOutput(
        name="test",
        table="iceberg.default.sales",
    )

    # Act
    result = step.external_datasets()

    # Assert
    actual = [(d.tiozin_namespace, d.tiozin_name) for d in result.outputs]
    expected = [("iceberg", "default.sales")]
    assert actual == expected


# ============================================================================
# Testing SparkTableOutput - Errors
# ============================================================================


@pytest.mark.parametrize(
    "table",
    ["sales", "default.sales", "iceberg.default.sales.extra"],
)
def test_output_should_raise_input_error_when_table_is_not_fully_qualified(table: str):
    # Act / Assert
    with pytest.raises(TiozinInputError):
        SparkTableOutput(
            name="test",
            table=table,
        )
