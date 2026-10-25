from unittest.mock import MagicMock, call, patch

import pytest

from tiozin.exceptions import NotInitializedError, TiozinInputError
from tiozin.family.tio_spark.runners.spark_runner import DEFAULT_LOGLEVEL, SparkRunner
from tiozin.logs.service import LogService


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


def test_spark_runner_should_raise_input_error_when_master_and_endpoint_are_provided():
    # Arrange
    master = "local[*]"
    endpoint = "sc://localhost:15002"

    # Act & Assert
    with pytest.raises(TiozinInputError):
        SparkRunner(master=master, endpoint=endpoint)


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
def test_setup_should_configure_jars_packages(session_class: MagicMock):
    # Arrange
    builder = session_class.builder
    builder.appName.return_value = builder
    builder.config.return_value = builder
    runner = SparkRunner(
        jars_packages=[
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0",
            "software.amazon.awssdk:bundle:2.20.0",
        ],
    )

    # Act
    with runner():
        pass

    # Assert
    actual = builder.config.call_args_list
    expected = call(
        "spark.jars.packages",
        "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,software.amazon.awssdk:bundle:2.20.0",
    )
    assert expected in actual


@patch("tiozin.family.tio_spark.runners.spark_runner.SparkSession")
def test_setup_should_not_configure_jars_packages_when_none_provided(session_class: MagicMock):
    # Arrange
    builder = session_class.builder
    builder.appName.return_value = builder
    builder.config.return_value = builder
    runner = SparkRunner()

    # Act
    with runner():
        pass

    # Assert
    actual = [config.args[0] for config in builder.config.call_args_list]
    assert "spark.jars.packages" not in actual


@patch("tiozin.family.tio_spark.runners.spark_runner.SparkSession")
@patch("tiozin.logs.log_service", new_callable=lambda: LogService(propagate=True))
def test_setup_should_not_log_endpoint_parameters(
    log_service: LogService,
    _session_class: MagicMock,
    caplog: pytest.LogCaptureFixture,
):
    # Arrange
    log_service.setup()
    runner = SparkRunner(endpoint="sc://spark.example.com:443/;token=fake-token-123;user_id=fake")

    # Act
    with runner():
        pass

    # Assert
    assert "Connecting to the Spark Connect server at sc://spark.example.com:443/" in caplog.text
    assert "fake-token-123" not in caplog.text
