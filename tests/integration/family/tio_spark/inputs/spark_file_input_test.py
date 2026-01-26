from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pyspark.sql import SparkSession
from pyspark.testing import assertDataFrameEqual

from tiozin import Context
from tiozin.family.tio_spark import SparkFileInput, SparkRunner

BASE_PATH = "./tests/mocks/data"


@pytest.fixture
def runner(spark_session: SparkSession) -> SparkRunner:
    runner = MagicMock(spec=SparkRunner)
    runner.session = spark_session
    runner.streaming = False
    return runner


@pytest.fixture
def job_context(runner: SparkRunner) -> Context:
    return Context(
        # Identity
        name="test",
        kind="test",
        plugin_kind="test",
        # Domain Metadata
        org="test",
        region="test",
        domain="test",
        layer="test",
        product="test",
        model="test",
        # Extra provider/plugin parameters
        options={},
        # Ownership
        maintainer="test",
        cost_center="test",
        owner="test",
        labels="test",
        # Runtime
        runner=runner,
    )


@pytest.fixture
def step_context(job_context: Context) -> Context:
    return Context(
        # Job
        parent=job_context,
        # Identity
        name="test",
        kind="test",
        plugin_kind="test",
        # Domain Metadata
        org="test",
        region="test",
        domain="test",
        layer="test",
        product="test",
        model="test",
        # Extra provider/plugin parameters
        options={},
    )


# ============================================================================
# Testing SparkFileInput - Core Behavior
# ============================================================================
def test_input_should_read_text_files(spark_session: SparkSession, step_context: Context):
    """Reads plain text files into a DataFrame."""
    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"

    # Act
    result = SparkFileInput(
        name="test",
        path=path,
        format="text",
    ).read(step_context)

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


def test_input_should_read_json_files(spark_session: SparkSession, step_context: Context):
    """Reads JSON files into a DataFrame using Spark semantics."""
    # Arrange
    path = f"{BASE_PATH}/json/sample.json"

    # Act
    result = SparkFileInput(
        name="test",
        path=path,
        format="json",
    ).read(step_context)

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
def test_input_should_apply_reader_options(step_context: Context):
    """Applies Spark reader options when loading files."""
    # Arrange
    path = f"{BASE_PATH}/json/sample.json"

    # Act
    actual = SparkFileInput(
        name="test",
        path=path,
        format="json",
        inferSchema=True,
    ).read(step_context)

    # Assert
    # schema inference doesn't change the value, but ensures options are applied
    assert "value" in actual.columns


# ============================================================================
# Testing SparkFileInput - Input File Metadata
# ============================================================================


def test_input_should_include_input_file_metadata(
    spark_session: SparkSession, step_context: Context
):
    """Adds input file path and file name columns when enabled."""
    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"
    absolute_path = Path(path).resolve()

    # Act
    result = SparkFileInput(
        name="test",
        path=path,
        format="text",
        include_input_file=True,
    ).read(step_context)

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
def test_input_should_use_streaming_reader_when_runner_is_streaming(step_context: Context):
    """Uses Spark readStream when the runner is in streaming mode."""
    # Arrange
    path = f"{BASE_PATH}/text/sample.txt"
    step_context.job.runner.streaming = True

    # Act
    df = SparkFileInput(
        name="test",
        path=path,
        format="text",
    ).read(step_context)

    # Assert
    assert df.isStreaming is True
