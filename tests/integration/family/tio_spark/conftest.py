import uuid
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest
from pyspark.sql import SparkSession

from tiozin import Context
from tiozin.compose import RunnerProxy
from tiozin.family.tio_spark import SparkRunner


@pytest.fixture(scope="session", autouse=True)
def spark_session(tmp_path_factory: pytest.TempPathFactory) -> Generator[SparkSession, Any, None]:
    builder: SparkSession.Builder = SparkSession.builder
    spark = (
        builder.appName("test")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.warehouse.dir", tmp_path_factory.mktemp(str(uuid.uuid4())))
        .getOrCreate()
    )
    token = RunnerProxy.active_session.set(spark)
    yield spark
    RunnerProxy.active_session.reset(token)
    spark.stop()


@pytest.fixture
def runner(spark_session: SparkSession) -> SparkRunner:
    runner = MagicMock(spec=SparkRunner)
    runner.streaming = False
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
