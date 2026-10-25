import os
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
from pyspark.sql.connect.session import SparkSession as SparkConnectSession

from tiozin.family.tio_spark import SparkRunner

# Starts a standalone Spark Connect server in a separate process. It runs out of process because
# PySpark refuses to start a local Spark Connect server while a classic SparkSession is active,
# and the Spark test fixtures keep one alive for the whole test session.
SPARK_CONNECT_SERVER = """
import sys

import pyspark
from pyspark.sql import SparkSession

(
    SparkSession.builder.master("local[1]")
    .config("spark.plugins", "org.apache.spark.sql.connect.SparkConnectPlugin")
    .config("spark.jars.packages", f"org.apache.spark:spark-connect_2.12:{pyspark.__version__}")
    .config("spark.connect.grpc.binding.port", sys.argv[1])
    .getOrCreate()
)
sys.stdin.read()
"""
SPARK_CONNECT_STARTUP_TIMEOUT = 300


@pytest.fixture(scope="module")
def spark_connect_endpoint() -> Generator[str, Any, None]:
    with socket.socket() as probe:
        probe.bind(("localhost", 0))
        port = probe.getsockname()[1]

    server = subprocess.Popen(
        [sys.executable, "-c", SPARK_CONNECT_SERVER, str(port)],
        stdin=subprocess.PIPE,
    )
    deadline = time.monotonic() + SPARK_CONNECT_STARTUP_TIMEOUT
    while True:
        try:
            socket.create_connection(("localhost", port), timeout=1).close()
            break
        except OSError:
            if server.poll() is not None or time.monotonic() > deadline:
                server.kill()
                raise RuntimeError("Spark Connect server failed to start") from None
            time.sleep(1)

    yield f"sc://localhost:{port}"

    server.terminate()
    server.wait()


# ============================================================================
# Testing SparkRunner - Spark Connect
# ============================================================================
# The Spark Connect client leaves SPARK_CONNECT_MODE_ENABLED in the environment, which would turn
# every SparkSession built afterwards in this process into a Spark Connect session.
@patch.dict(os.environ)
def test_setup_should_create_spark_connect_session_when_endpoint_is_provided(
    spark_connect_endpoint: str,
):
    # Arrange
    runner = SparkRunner(endpoint=spark_connect_endpoint)

    # Act
    with runner():
        result = runner.session

    # Assert
    assert isinstance(result, SparkConnectSession)
