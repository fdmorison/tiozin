import uuid
from collections.abc import Generator
from typing import Any

import pytest
from pyspark.sql import SparkSession

from tests.stubs import JobStub, RunnerStub
from tiozin import Context
from tiozin.family.tio_spark import SparkRunner


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
def spark_runner_stub(runner_stub: RunnerStub, spark: SparkSession) -> RunnerStub:
    runner_stub._session = spark
    return runner_stub


@pytest.fixture(autouse=True)
def spark_job_stub(job_stub: JobStub, spark_runner_stub: RunnerStub) -> JobStub:
    job_stub.runner = spark_runner_stub
    return job_stub


@pytest.fixture(autouse=True)
def spark_session(spark_job_stub: JobStub) -> Generator[Any, Any, None]:
    with Context.for_job(spark_job_stub) as context:
        yield context.runner.session


@pytest.fixture
def spark_runner() -> Generator[SparkRunner, Any, None]:
    """Returns a raw DuckdbRunner already set up with an in-memory connection."""
    runner: SparkRunner = SparkRunner().__wrapped__
    runner.setup()
    yield runner
    runner.teardown()
