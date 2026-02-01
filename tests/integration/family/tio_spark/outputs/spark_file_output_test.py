from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin import Context
from tiozin.family.tio_spark.outputs.file_output import SparkFileOutput

BASE_PATH = "./tests/mocks/data"


# ============================================================================
# Testing SparkFileOutput - Integration
# ============================================================================


def test_output_should_write_files(
    spark_session: SparkSession, tmp_path: Path, step_context: Context
):
    """Writes a DataFrame to disk using Parquet format."""
    # Arrange
    input_data = spark_session.createDataFrame(
        [
            ("hello", 1),
            ("world", 2),
        ],
        schema="word STRING, count INT",
    )
    output_path = tmp_path / "parquet"

    # Act
    SparkFileOutput(
        name="test",
        path=str(output_path),
        format="parquet",
        mode="overwrite",
    ).write(step_context, input_data).save()

    # Assert
    actual = spark_session.read.parquet(str(output_path))
    expected = spark_session.createDataFrame(
        [
            ("hello", 1),
            ("world", 2),
        ],
        schema="word STRING, count INT",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_output_should_write_another_format_of_files(
    spark_session: SparkSession, tmp_path: Path, step_context: Context
):
    """Writes a DataFrame to disk using JSON format."""
    # Arrange
    input_data = spark_session.createDataFrame(
        [
            ("hello",),
            ("spark",),
        ],
        schema="value STRING",
    )
    output_path = tmp_path / "json"

    # Act
    SparkFileOutput(
        name="test",
        path=str(output_path),
        format="json",
        mode="overwrite",
    ).write(step_context, input_data).save()

    # Assert
    actual = spark_session.read.json(str(output_path))
    expected = spark_session.createDataFrame(
        [
            ("hello",),
            ("spark",),
        ],
        schema="value STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_output_should_write_partitioned_data(
    spark_session: SparkSession, tmp_path: Path, step_context: Context
):
    """Writes partitioned data when partition_by is provided."""
    # Arrange
    input_data = spark_session.createDataFrame(
        [
            ("2024-01-01", "hello"),
            ("2024-01-02", "world"),
        ],
        schema="date STRING, value STRING",
    )
    output_path = tmp_path / "partitioned"

    # Act
    SparkFileOutput(
        name="test",
        path=str(output_path),
        format="parquet",
        mode="overwrite",
        partition_by=["date"],
    ).write(step_context, input_data).save()

    # Assert
    actual = spark_session.read.parquet(str(output_path))
    expected = spark_session.createDataFrame(
        [
            ("hello", "2024-01-01"),
            ("world", "2024-01-02"),
        ],
        schema="value STRING, date STRING",
    ).selectExpr(
        "value",
        "CAST(date AS DATE) AS date",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)


def test_output_should_apply_writer_options(
    spark_session: SparkSession, tmp_path: Path, step_context: Context
):
    """Applies Spark writer options when writing files."""
    # Arrange
    input_data = spark_session.createDataFrame(
        [
            ("hello",),
            ("world",),
        ],
        schema="value STRING",
    )
    output_path = tmp_path / "compressed"

    # Act
    SparkFileOutput(
        name="test",
        path=str(output_path),
        format="json",
        mode="overwrite",
        compression="gzip",
    ).write(step_context, input_data).save()

    # Assert
    actual = spark_session.read.json(str(output_path))
    expected = spark_session.createDataFrame(
        [
            ("hello",),
            ("world",),
        ],
        schema="value STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=False)
