from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin.family.tio_spark.inputs.file_input import SparkFileInput

# ============================================================================
# Helpers
# ============================================================================


class DummyRunner:
    def __init__(self, spark: SparkSession, streaming: bool = False):
        self.session = spark
        self.streaming = streaming


class DummyJob:
    def __init__(self, runner):
        self.runner = runner


class DummyContext:
    def __init__(self, runner):
        self.job = DummyJob(runner)


BASE_PATH = "./tests/mocks/data"


# ============================================================================
# Testing SparkFileInput - Core Behavior
# ============================================================================


def test_input_should_read_text_files(spark_session: SparkSession):
    """Reads plain text files into a DataFrame."""
    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"
    context = DummyContext(
        DummyRunner(spark_session),
    )

    # Act
    result = SparkFileInput(
        name="test",
        path=path,
        format="text",
    ).read(context)

    # Assert
    actual = result
    expected = spark_session.createDataFrame(
        [
            ("hello world",),
            ("hello spark",),
        ],
        schema="`value` STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_input_should_read_json_files(spark_session: SparkSession):
    """Reads JSON files into a DataFrame using Spark semantics."""
    # Arrange
    path = f"{BASE_PATH}/json/sample.json"
    context = DummyContext(
        DummyRunner(spark_session),
    )

    # Act
    result = SparkFileInput(
        name="test",
        path=path,
        format="json",
    ).read(context)

    # Assert
    actual = result
    expected = spark_session.createDataFrame(
        [
            ("hello world",),
            ("hello spark",),
        ],
        schema="`value` STRING",
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)


# ============================================================================
# Testing SparkFileInput - Reader Options
# ============================================================================


def test_input_should_apply_reader_options(spark_session: SparkSession):
    """Applies Spark reader options when loading files."""
    # Arrange
    path = f"{BASE_PATH}/json/sample.json"
    context = DummyContext(
        DummyRunner(spark_session),
    )

    # Act
    actual = SparkFileInput(
        name="test",
        path=path,
        format="json",
        inferSchema=True,
    ).read(context)

    # Assert
    # schema inference doesn't change the value, but ensures options are applied
    assert "value" in actual.columns


# ============================================================================
# Testing SparkFileInput - Input File Metadata
# ============================================================================


def test_input_should_include_input_file_metadata(spark_session: SparkSession):
    """Adds input file path and file name columns when enabled."""
    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"
    absolute_path = Path(path).resolve()
    context = DummyContext(
        DummyRunner(spark_session),
    )

    # Act
    result = SparkFileInput(
        name="test",
        path=path,
        format="text",
        include_input_file=True,
    ).read(context)

    # Assert
    actual = result
    expected = spark_session.createDataFrame(
        [
            ("hello world", f"file://{absolute_path}", "sample.txt"),
            ("hello spark", f"file://{absolute_path}", "sample.txt"),
        ],
        schema="""
            value STRING,
            input_file_path STRING,
            input_file_name STRING
        """,
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)


# ============================================================================
# Testing SparkFileInput - Streaming Mode
# ============================================================================


def test_input_should_use_streaming_reader_when_runner_is_streaming(spark_session: SparkSession):
    """Uses Spark readStream when the runner is in streaming mode."""
    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"
    context = DummyContext(
        DummyRunner(spark_session, streaming=True),
    )

    # Act
    df = SparkFileInput(
        name="test",
        path=path,
        format="text",
    ).read(context)

    # Assert
    assert df.isStreaming is True
