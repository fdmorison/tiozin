from unittest.mock import MagicMock, patch

import pytest
from pyspark.sql.connect.dataframe import DataFrame as ConnectDataFrame
from pyspark.sql.connect.readwriter import DataFrameWriter as ConnectDataFrameWriter
from pyspark.sql.connect.streaming.readwriter import DataStreamWriter as ConnectDataStreamWriter

from tiozin.exceptions import NotInitializedError
from tiozin.family.tio_spark.runners.spark_runner import DEFAULT_LOGLEVEL, SparkRunner


# ============================================================================
# Testing SparkRunner initialization
# ============================================================================
def test_spark_runner_should_use_default_values_when_no_parameters_provided():
    # Act
    runner = SparkRunner()

    # Assert
    actual = (
        runner.master,
        runner.endpoint,
        runner.enable_hive_support,
        runner.log_level,
        runner.jars_packages,
    )
    expected = (None, None, False, DEFAULT_LOGLEVEL, [])
    assert actual == expected


def test_spark_runner_should_store_master_parameter():
    # Arrange
    master = "local[*]"

    # Act
    runner = SparkRunner(master=master)

    # Assert
    actual = runner.master
    expected = "local[*]"
    assert actual == expected


def test_spark_runner_should_store_endpoint_parameter():
    # Arrange
    endpoint = "sc://localhost:15002"

    # Act
    runner = SparkRunner(endpoint=endpoint)

    # Assert
    actual = runner.endpoint
    expected = "sc://localhost:15002"
    assert actual == expected


def test_spark_runner_should_store_enable_hive_support_parameter():
    # Arrange
    enable_hive_support = True

    # Act
    runner = SparkRunner(enable_hive_support=enable_hive_support)

    # Assert
    actual = runner.enable_hive_support
    expected = True
    assert actual == expected


def test_spark_runner_should_store_log_level_parameter():
    # Arrange
    log_level = "INFO"

    # Act
    runner = SparkRunner(log_level=log_level)

    # Assert
    actual = runner.log_level
    expected = "INFO"
    assert actual == expected


def test_spark_runner_should_store_jars_packages_as_list():
    # Arrange
    jars_packages = [
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0",
        "software.amazon.awssdk:bundle:2.20.0",
    ]

    # Act
    runner = SparkRunner(jars_packages=jars_packages)

    # Assert
    actual = runner.jars_packages
    expected = [
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0",
        "software.amazon.awssdk:bundle:2.20.0",
    ]
    assert actual == expected


def test_spark_runner_should_convert_single_jar_package_to_list():
    # Arrange
    jars_packages = "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0"

    # Act
    runner = SparkRunner(jars_packages=jars_packages)

    # Assert
    actual = runner.jars_packages
    expected = ["org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0"]
    assert actual == expected


def test_spark_runner_should_store_extra_options():
    # Arrange
    options = {
        "spark.executor.memory": "4g",
        "spark.sql.shuffle.partitions": "200",
    }

    # Act
    runner = SparkRunner(**options)

    # Assert
    actual = runner.options
    expected = {
        "spark.executor.memory": "4g",
        "spark.sql.shuffle.partitions": "200",
    }
    assert actual == expected


# ============================================================================
# Testing SparkRunner session property
# ============================================================================
def test_spark_runner_session_should_raise_not_initialized_error_before_setup():
    # Arrange
    runner = SparkRunner()

    # Act & Assert
    with pytest.raises(NotInitializedError):
        _ = runner.session


# ============================================================================
# Testing SparkRunner setup
# ============================================================================
@patch("tiozin.family.tio_spark.runners.spark_runner.SparkSession")
def test_setup_should_not_log_endpoint_parameters(_: MagicMock):
    # Arrange
    runner: SparkRunner = SparkRunner(endpoint="sc://localhost:15002/;token=abc123").__wrapped__

    # Act
    with patch.object(runner, "info") as info:
        runner.setup()

    # Assert
    assert "abc123" not in str(info.call_args_list)


@patch("tiozin.family.tio_spark.runners.spark_runner.SparkSession")
def test_setup_should_not_set_log_level_when_endpoint_is_set(spark_session_cls: MagicMock):
    # Arrange
    builder = spark_session_cls.builder
    builder.appName.return_value = builder
    builder.config.return_value = builder
    builder.remote.return_value = builder
    session = builder.getOrCreate.return_value
    runner: SparkRunner = SparkRunner(endpoint="sc://localhost:15002").__wrapped__

    # Act
    runner.setup()

    # Assert
    session.sparkContext.setLogLevel.assert_not_called()


# ============================================================================
# Testing SparkRunner run with Spark Connect plans
# ============================================================================
def test_run_should_count_connect_dataframe():
    # Arrange
    runner: SparkRunner = SparkRunner().__wrapped__
    plan = MagicMock(spec=ConnectDataFrame)

    # Act
    runner.run(plan)

    # Assert
    plan.count.assert_called_once()


def test_run_should_save_connect_dataframe_writer():
    # Arrange
    runner: SparkRunner = SparkRunner().__wrapped__
    plan = MagicMock(spec=ConnectDataFrameWriter)

    # Act
    runner.run(plan)

    # Assert
    plan.save.assert_called_once()


def test_run_should_await_connect_data_stream_writer_termination():
    # Arrange
    runner: SparkRunner = SparkRunner().__wrapped__
    plan = MagicMock(spec=ConnectDataStreamWriter)

    # Act
    runner.run(plan)

    # Assert
    plan.start.return_value.awaitTermination.assert_called_once()
