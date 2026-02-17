from pathlib import Path

import pytest
from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin import Context
from tiozin.family.tio_spark import SparkFileInput

BASE_PATH = "./tests/mocks/data"


# ============================================================================
# Testing SparkFileInput - Core Behavior
# ============================================================================
def test_input_should_read_text_files(spark_session: SparkSession):
    """Reads plain text files into a DataFrame."""
    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"

    # Act
    result = SparkFileInput(
        name="test",
        path=path,
        format="text",
    ).read()

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

    # Act
    result = SparkFileInput(
        name="test",
        path=path,
        format="json",
    ).read()

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
def test_input_should_apply_reader_options():
    """Applies Spark reader options when loading files."""
    # Arrange
    path = f"{BASE_PATH}/json/sample.json"

    # Act
    actual = SparkFileInput(
        name="test",
        path=path,
        format="json",
        inferSchema=True,
    ).read()

    # Assert
    # schema inference doesn't change the value, but ensures options are applied
    assert "value" in actual.columns


# ============================================================================
# Testing SparkFileInput - Input File Metadata
# ============================================================================


@pytest.mark.parametrize(
    "filename,filestem,filetype",
    [
        ("sample", "sample", ""),
        ("sample.txt", "sample", "txt"),
    ],
)
def test_input_should_explode_filepath(
    filename: str,
    filestem: str,
    filetype: str,
    spark_session: SparkSession,
):
    """Expands filepath into semantic columns when enabled."""
    # Arrange
    path = f"{BASE_PATH}/text/{filename}"
    dirpath = Path(path).resolve().parent
    filepath = f"file://{dirpath}/{filename}"

    # Act
    result = SparkFileInput(
        name="test",
        path=path,
        format="text",
        explode_filepath=True,
    ).read()

    # Assert
    actual = result
    expected = spark_session.createDataFrame(
        [
            (
                "hello world",
                24,
                f"file://{dirpath}",
                "text",
                filepath,
                filename,
                filestem,
                filetype,
            ),
            (
                "hello spark",
                24,
                f"file://{dirpath}",
                "text",
                filepath,
                filename,
                filestem,
                filetype,
            ),
        ],
        schema="""
            value    STRING,
            filesize BIGINT,
            dirpath  STRING,
            dirname  STRING,
            filepath STRING,
            filename STRING,
            filestem STRING,
            filetype STRING
        """,
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)


# ============================================================================
# Testing SparkFileInput - Streaming Mode
# ============================================================================
def test_input_should_use_streaming_reader_when_runner_is_streaming():
    """Uses Spark readStream when the runner is in streaming mode."""
    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"
    Context.current().job.runner.streaming = True

    # Act
    df = SparkFileInput(
        name="test",
        path=path,
        format="text",
    ).read()

    # Assert
    assert df.isStreaming is True
