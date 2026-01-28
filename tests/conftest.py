import uuid
from collections.abc import Generator
from typing import Any

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark_session(tmp_path_factory: pytest.TempPathFactory) -> Generator[Any, Any, None]:
    warehouse_name = f"spark-warehouse-{uuid.uuid4().hex}"
    warehouse_dir = tmp_path_factory.mktemp(warehouse_name)
    spark = (
        SparkSession.builder.master("local[1]")
        .appName("test")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.warehouse.dir", str(warehouse_dir))
        .getOrCreate()
    )
    yield spark
    spark.stop()
