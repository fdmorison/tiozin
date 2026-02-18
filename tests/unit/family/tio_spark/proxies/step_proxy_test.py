from pyspark.sql import SparkSession

from tiozin.family.tio_spark import SparkWordCountTransform
from tiozin.utils.runtime import tio_alias

# =============================================================================
# Testing SparkStepProxy._register_view — slug as view name
# =============================================================================


def test_proxy_should_register_view_using_step_slug(spark: SparkSession):
    """Temp view is registered under the slug, not the raw step name."""
    # Arrange
    step = SparkWordCountTransform(name="my word count step")
    df = spark.createDataFrame([("hello world",)], schema="`value` STRING")

    # Act
    result = step.transform(df)

    # Assert
    actual = tio_alias(result)
    expected = "my_word_count_step"
    assert actual == expected


def test_proxy_should_make_view_queryable_by_slug(spark: SparkSession):
    """After registration, the temp view is accessible by its slug in Spark SQL."""
    # Arrange
    step = SparkWordCountTransform(name="my word count step")
    df = spark.createDataFrame([("hello world",)], schema="`value` STRING")

    # Act
    step.transform(df)

    # Assert — slug is a valid Spark SQL identifier and the view is queryable
    actual = spark.sql("SELECT * FROM my_word_count_step").collect()
    assert len(actual) > 0


def test_proxy_should_preserve_slug_when_name_has_special_characters(
    spark: SparkSession,
):
    """Slug handles hyphens, mixed case, and extra spaces in the step name."""
    # Arrange
    step = SparkWordCountTransform(name="Word Count - 2024!")
    df = spark.createDataFrame([("hello world",)], schema="`value` STRING")

    # Act
    result = step.transform(df)

    # Assert
    actual = tio_alias(result)
    expected = "word_count_2024"
    assert actual == expected
