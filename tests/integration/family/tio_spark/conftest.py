import uuid
from collections.abc import Generator
from typing import Any

import pytest
from pyspark.sql import SparkSession

from tiozin.compose import RunnerProxy


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
