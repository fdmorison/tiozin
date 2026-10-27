import uuid
from collections.abc import Generator
from typing import Any

import pytest
from pyspark.sql import SparkSession

from tests.stubs import JobStub, RunnerStub
from tiozin import Context


@pytest.fixture(scope="session", autouse=True)
def spark(tmp_path_factory: pytest.TempPathFactory) -> Generator[SparkSession, Any, None]:
    iceberg_warehouse = tmp_path_factory.mktemp("iceberg")
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("SPARK_HOME", raising=False)
        builder: SparkSession.Builder = SparkSession.builder
        spark = (
            builder.appName("test")
            # Session
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.warehouse.dir", tmp_path_factory.mktemp(str(uuid.uuid4())))
            # Packages
            .config(
                "spark.jars.packages",
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1,"
                "io.delta:delta-spark_2.12:3.2.0,"
                "org.xerial:sqlite-jdbc:3.46.1.3",
            )
            # Extensions
            .config(
                "spark.sql.extensions",
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions,"
                "io.delta.sql.DeltaSparkSessionExtension",
            )
            # Delta catalog (session catalog)
            .config(
                "spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog"
            )
            # Iceberg catalog (JDBC on SQLite)
            .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
            .config("spark.sql.catalog.iceberg.type", "jdbc")
            .config("spark.sql.catalog.iceberg.uri", f"jdbc:sqlite:{iceberg_warehouse}/catalog.db")
            .config("spark.sql.catalog.iceberg.jdbc.schema-version", "V1")
            .config("spark.sql.catalog.iceberg.warehouse", str(iceberg_warehouse))
            .getOrCreate()
        )
    yield spark
    spark.stop()


@pytest.fixture(autouse=True)
def spark_runner(runner_stub: RunnerStub, spark: SparkSession) -> RunnerStub:
    runner_stub._session = spark
    return runner_stub


@pytest.fixture(autouse=True)
def spark_job(job_stub: JobStub, spark_runner: RunnerStub) -> JobStub:
    job_stub.runner = spark_runner
    return job_stub


@pytest.fixture(autouse=True)
def spark_job_context(spark_job: JobStub, job_context: Context) -> Context:
    return job_context
