from pathlib import Path

from pyspark.sql import SparkSession

from tiozin import Context, Schema
from tiozin.family.tio_spark import SparkFileOutput, SparkWordCountTransform
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


# =============================================================================
# Testing SparkStepProxy.write — schema captured from input data
# =============================================================================


def test_write_should_capture_schema_from_input_when_output_is_not_dataframe(
    spark: SparkSession, tmp_path: Path
):
    """
    Regression test: write() must capture the schema from the input DataFrame
    even when the step outputs a non-DataFrame (e.g. DataFrameWriter).
    Without this, context.schema stays None and the schema is absent from lineage.
    """
    # Arrange
    step = SparkFileOutput(name="orders_output", path=str(tmp_path / "out"))
    df = spark.createDataFrame(
        [(1, "alice")],
        schema="`id` INT, `name` STRING",
    )

    # Act
    step.write(df)

    # Assert — schema is recorded on the catalog output dataset
    outputs = Context.current().catalog.get_outputs(step)
    actual = isinstance(outputs[0].tiozin_schema, Schema)
    expected = True
    assert actual == expected
