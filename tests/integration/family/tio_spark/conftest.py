import uuid
from collections.abc import Generator
from typing import Any

import pytest
from pyspark.sql import SparkSession

from tests.stubs import JobStub, RunnerStub
from tiozin import Context


@pytest.fixture(scope="session", autouse=True)
def spark(tmp_path_factory: pytest.TempPathFactory) -> Generator[SparkSession, Any, None]:
    builder: SparkSession.Builder = SparkSession.builder
    spark = (
        builder.appName("test")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.warehouse.dir", tmp_path_factory.mktemp(str(uuid.uuid4())))
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
def spark_job_context(job_context: Context, spark_runner: RunnerStub) -> None:
    job_context.runner = spark_runner
    return job_context
