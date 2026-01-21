import pytest
from pyspark.sql import SparkSession

# noop: trigger patch release 1.2.1


@pytest.fixture(scope="module")
def spark_session():
    return (
        SparkSession.builder.master("local[1]")
        .appName("test")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
