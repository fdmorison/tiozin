from unittest.mock import MagicMock, patch

from tiozin.family.tio_spark.runners.spark_iceberg_runner import SparkIcebergRunner


# ============================================================================
# Testing SparkIcebergRunner setup
# ============================================================================
@patch("tiozin.family.tio_spark.runners.spark_runner.SparkSession")
def test_setup_should_create_session(spark_session_cls: MagicMock):
    # Arrange
    builder = spark_session_cls.builder
    builder.appName.return_value = builder
    builder.config.return_value = builder
    session = builder.getOrCreate.return_value
    runner: SparkIcebergRunner = SparkIcebergRunner(
        catalog_name="local",
        catalog_type="hadoop",
    ).__wrapped__

    # Act
    runner.setup()

    # Assert
    actual = runner.session
    expected = session
    assert actual == expected
