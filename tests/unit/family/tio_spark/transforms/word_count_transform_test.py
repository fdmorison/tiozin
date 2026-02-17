from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin.family.tio_spark.transforms.word_count_transform import (
    SparkWordCountTransform,
)

# ============================================================================
# Testing SparkWordCountTransform - Core Behavior
# ============================================================================


def test_transform_should_count_words(spark: SparkSession):
    """Counts word occurrences across all input rows."""
    # Arrange
    input = spark.createDataFrame(
        [
            ("lorem ipsum dolor sit amet",),
            ("lorem lorem dolor sit sit sit sit",),
        ],
        schema="`value` STRING",
    )

    # Act
    actual = SparkWordCountTransform(
        name="test",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            ("amet", 1),
            ("dolor", 2),
            ("ipsum", 1),
            ("lorem", 3),
            ("sit", 5),
        ],
        schema="`word` STRING, `count` BIGINT",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_return_empty_dataframe_when_input_is_empty(
    spark: SparkSession,
):
    """Returns an empty result when the input DataFrame has no rows."""
    # Arrange
    input = spark.createDataFrame(
        [],
        schema="`value` STRING",
    )

    # Act
    actual = SparkWordCountTransform(
        name="test",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [],
        schema="`word` STRING, `count` BIGINT",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


# ============================================================================
# Testing SparkWordCountTransform - Lowercase Normalization
# ============================================================================


def test_transform_should_normalize_words_to_lowercase(
    spark: SparkSession,
):
    """Normalizes tokens to lowercase before counting by default."""
    # Arrange
    input = spark.createDataFrame(
        [
            ("Lorem IPSUM DoLor SIT amET",),
            ("lorem ipsum doLOR sit SIT sIt Sit",),
        ],
        schema="`value` STRING",
    )

    # Act
    actual = SparkWordCountTransform(
        name="test",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            ("amet", 1),
            ("dolor", 2),
            ("ipsum", 2),
            ("lorem", 2),
            ("sit", 5),
        ],
        schema="`word` STRING, `count` BIGINT",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_preserve_case_when_lowercase_is_disabled(
    spark: SparkSession,
):
    """Preserves original token casing when lowercase normalization is disabled."""
    # Arrange
    input = spark.createDataFrame(
        [
            ("Hello hello HELLO",),
        ],
        schema="`value` STRING",
    )

    # Act
    actual = SparkWordCountTransform(
        name="test",
        lowercase=False,
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            ("HELLO", 1),
            ("Hello", 1),
            ("hello", 1),
        ],
        schema="`word` STRING, `count` BIGINT",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


# ============================================================================
# Testing SparkWordCountTransform - Tokenization Rules
# ============================================================================


def test_transform_should_remove_punctuation(
    spark: SparkSession,
):
    """Splits words correctly by removing punctuation and special characters."""
    # Arrange
    input = spark.createDataFrame(
        [
            ("lorem.ipsum, dolor-sit... amet-----",),
            (",lorem! lorem dolor sit\\sit+sit#sit",),
        ],
        schema="`value` STRING",
    )

    # Act
    actual = SparkWordCountTransform(
        name="test",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            ("amet", 1),
            ("dolor", 2),
            ("ipsum", 1),
            ("lorem", 3),
            ("sit", 5),
        ],
        schema="`word` STRING, `count` BIGINT",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_preserve_apostrophes(
    spark: SparkSession,
):
    """Keeps apostrophes as part of tokens during word splitting."""
    # Arrange
    input = spark.createDataFrame(
        [
            ("lorem's ipsum' dolor sit amet",),
            ("lorem lorem dolor sit sit sit sit",),
        ],
        schema="`value` STRING",
    )

    # Act
    actual = SparkWordCountTransform(
        name="test",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            ("amet", 1),
            ("dolor", 2),
            ("ipsum'", 1),
            ("lorem", 2),
            ("lorem's", 1),
            ("sit", 5),
        ],
        schema="`word` STRING, `count` BIGINT",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_handle_unicode_characters(
    spark: SparkSession,
):
    """Correctly tokenizes and counts Unicode characters."""
    # Arrange
    input = spark.createDataFrame(
        [
            ("olá mundo café",),
            ("olá olá mundo",),
        ],
        schema="`value` STRING",
    )

    # Act
    actual = SparkWordCountTransform(
        name="test",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            ("café", 1),
            ("mundo", 2),
            ("olá", 3),
        ],
        schema="`word` STRING, `count` BIGINT",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


# ============================================================================
# Testing SparkWordCountTransform - Grouping Behavior
# ============================================================================


def test_transform_should_count_words_grouped_by_single_column(
    spark: SparkSession,
):
    """Scopes word counts by a single grouping column."""
    # Arrange
    input = spark.createDataFrame(
        [
            ("hamlet", "lorem's ipsum' dolor sit amet"),
            ("sonnet", "lorem lorem dolor sit sit sit sit"),
        ],
        schema="`doc_id` STRING, `value` STRING",
    )

    # Act
    actual = SparkWordCountTransform(
        name="test",
        count_by="doc_id",
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            ("hamlet", "amet", 1),
            ("hamlet", "dolor", 1),
            ("hamlet", "ipsum'", 1),
            ("hamlet", "lorem's", 1),
            ("hamlet", "sit", 1),
            ("sonnet", "dolor", 1),
            ("sonnet", "lorem", 2),
            ("sonnet", "sit", 4),
        ],
        schema="`doc_id` STRING, `word` STRING, `count` BIGINT",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_transform_should_count_words_grouped_by_multiple_columns(
    spark: SparkSession,
):
    """Scopes word counts by multiple grouping columns."""
    # Arrange
    input = spark.createDataFrame(
        [
            ("hamlet", "act1", "hello world"),
            ("hamlet", "act2", "hello hello"),
            ("sonnet", "act1", "world world world"),
        ],
        schema="`play` STRING, `act` STRING, `value` STRING",
    )

    # Act
    actual = SparkWordCountTransform(
        name="test",
        count_by=["play", "act"],
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            ("hamlet", "act1", "hello", 1),
            ("hamlet", "act1", "world", 1),
            ("hamlet", "act2", "hello", 2),
            ("sonnet", "act1", "world", 3),
        ],
        schema="`play` STRING, `act` STRING, `word` STRING, `count` BIGINT",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)


# ============================================================================
# Testing SparkWordCountTransform - Parameterization (Canonical Test)
# ============================================================================


def test_transform_should_apply_all_parameters(
    spark: SparkSession,
):
    """Applies all constructor parameters to the transformation behavior."""
    # Arrange
    input = spark.createDataFrame(
        [
            ("doc1", "Hello HELLO"),
            ("doc2", "Hello world"),
        ],
        schema="`doc_id` STRING, `text` STRING",
    )

    # Act
    actual = SparkWordCountTransform(
        name="test",
        content_field="text",
        count_by="doc_id",
        lowercase=False,
    ).transform(input)

    # Assert
    expected = spark.createDataFrame(
        [
            ("doc1", "HELLO", 1),
            ("doc1", "Hello", 1),
            ("doc2", "Hello", 1),
            ("doc2", "world", 1),
        ],
        schema="`doc_id` STRING, `word` STRING, `count` BIGINT",
    )

    assertDataFrameEqual(actual, expected, checkRowOrder=True)
