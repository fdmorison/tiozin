import pytest
from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin.exceptions import TiozinInputError
from tiozin.family.tio_spark import SparkDeduplicateTransform

# ============================================================================
# Testing SparkDeduplicateTransform - All Columns
# ============================================================================


@pytest.mark.parametrize("keys", [None, []])
def test_transform_should_keep_one_row_per_identical_rows(spark: SparkSession, keys: list[str]):
    """Collapses rows equal in all columns and keeps rows that differ in any column."""
    # Arrange
    input = spark.createDataFrame(
        [
            (1, "Alice"),
            (1, "Alice"),
            (1, "Alicia"),
        ],
        schema="`customer_id` INT, `name` STRING",
    )

    # Act
    result = SparkDeduplicateTransform(
        name="test",
        keys=keys,
    ).transform(input)

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "Alice"),
            (1, "Alicia"),
        ],
        schema="`customer_id` INT, `name` STRING",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# Testing SparkDeduplicateTransform - Keys Only
# ============================================================================


def test_transform_should_keep_one_row_per_key(spark: SparkSession):
    """Collapses rows that share the same key into a single row."""
    # Arrange
    input = spark.createDataFrame(
        [
            (1, "Alice", 1),
            (1, "Alicia", 2),
            (2, "Bob", 1),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )

    # Act
    result = SparkDeduplicateTransform(
        name="test",
        keys="customer_id",
        order_by="version",
    ).transform(input)

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "Alicia", 2),
            (2, "Bob", 1),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_keep_one_row_per_composite_key(spark: SparkSession):
    """Treats rows as duplicates only when all key columns match."""
    # Arrange
    input = spark.createDataFrame(
        [
            (1, "home", "Lorem Street", 1),
            (1, "home", "Dolor Street", 2),
            (1, "work", "Ipsum Avenue", 1),
        ],
        schema="`customer_id` INT, `address_type` STRING, `street` STRING, `version` INT",
    )

    # Act
    result = SparkDeduplicateTransform(
        name="test",
        keys=["customer_id", "address_type"],
        order_by="version",
    ).transform(input)

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "home", "Dolor Street", 2),
            (1, "work", "Ipsum Avenue", 1),
        ],
        schema="`customer_id` INT, `address_type` STRING, `street` STRING, `version` INT",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# Testing SparkDeduplicateTransform - Ordering
# ============================================================================


def test_transform_should_keep_last_row_by_default(spark: SparkSession):
    """Keeps the row with the highest order_by value per key when keep is omitted."""
    # Arrange
    input = spark.createDataFrame(
        [
            (1, "Alice", 1),
            (1, "Alicia", 3),
            (1, "Ally", 2),
            (2, "Bob", 1),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )

    # Act
    result = SparkDeduplicateTransform(
        name="test",
        keys="customer_id",
        order_by="version",
    ).transform(input)

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "Alicia", 3),
            (2, "Bob", 1),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_keep_first_row_when_keep_is_first(spark: SparkSession):
    """Keeps the row with the lowest order_by value per key."""
    # Arrange
    input = spark.createDataFrame(
        [
            (1, "Alice", 1),
            (1, "Alicia", 3),
            (1, "Ally", 2),
            (2, "Bob", 1),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )

    # Act
    result = SparkDeduplicateTransform(
        name="test",
        keys="customer_id",
        order_by="version",
        keep="first",
    ).transform(input)

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "Alice", 1),
            (2, "Bob", 1),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_compare_all_columns_except_order_by_when_keys_are_omitted(
    spark: SparkSession,
):
    """Treats rows equal in every non-order_by column as duplicates and keeps the last one."""
    # Arrange
    input = spark.createDataFrame(
        [
            (1, "Alice", 1),
            (1, "Alice", 3),
            (1, "Alicia", 2),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )

    # Act
    result = SparkDeduplicateTransform(
        name="test",
        order_by="version",
    ).transform(input)

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "Alice", 3),
            (1, "Alicia", 2),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_break_ties_with_next_order_by_column(spark: SparkSession):
    """Uses later order_by columns to decide between rows tied on earlier ones."""
    # Arrange
    input = spark.createDataFrame(
        [
            (1, "Alice", 2, 10),
            (1, "Alicia", 2, 30),
            (1, "Ali", 1, 99),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT, `ingested_at` INT",
    )

    # Act
    result = SparkDeduplicateTransform(
        name="test",
        keys="customer_id",
        order_by=["version", "ingested_at"],
    ).transform(input)

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "Alicia", 2, 30),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT, `ingested_at` INT",
    )
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize("keep", ["first", "last"])
def test_transform_should_keep_row_with_value_over_null_order_by(spark: SparkSession, keep: str):
    """Never keeps a row with a null order_by value when a row with a value exists."""
    # Arrange
    input = spark.createDataFrame(
        [
            (1, "Alice", None),
            (1, "Alicia", 2),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )

    # Act
    result = SparkDeduplicateTransform(
        name="test",
        keys="customer_id",
        order_by="version",
        keep=keep,
    ).transform(input)

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "Alicia", 2),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )
    assertDataFrameEqual(actual, expected)


def test_transform_should_keep_one_row_when_order_by_ties(spark: SparkSession):
    """Keeps a single row per key when rows tie on every order_by field."""
    # Arrange
    input = spark.createDataFrame(
        [
            (1, "Alice", 2),
            (1, "Alice", 2),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )

    # Act
    result = SparkDeduplicateTransform(
        name="test",
        keys="customer_id",
        order_by="version",
    ).transform(input)

    # Assert
    actual = result
    expected = spark.createDataFrame(
        [
            (1, "Alice", 2),
        ],
        schema="`customer_id` INT, `name` STRING, `version` INT",
    )
    assertDataFrameEqual(actual, expected)


# ============================================================================
# Testing SparkDeduplicateTransform - Validation
# ============================================================================


def test_init_should_raise_input_error_when_keep_is_invalid():
    # Act & Assert
    with pytest.raises(
        TiozinInputError, match=r"Invalid value 'middle'\. Must be one of: first, last"
    ):
        SparkDeduplicateTransform(
            name="test",
            keys="customer_id",
            order_by="version",
            keep="middle",
        )


def test_init_should_raise_input_error_when_keep_lacks_order_by():
    # Act & Assert
    with pytest.raises(TiozinInputError, match="`keep` requires `order_by`"):
        SparkDeduplicateTransform(
            name="test",
            keys="customer_id",
            keep="first",
        )
