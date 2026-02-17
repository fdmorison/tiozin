from collections.abc import Generator
from typing import Any

import duckdb
import pytest
from duckdb import DuckDBPyConnection

from tests.stubs import JobStub, RunnerStub
from tiozin import Context
from tiozin.family.tio_duckdb import DuckdbRunner


@pytest.fixture(scope="session", autouse=True)
def duckdb_conn() -> Generator[DuckDBPyConnection, Any, None]:
    conn = duckdb.connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def duckdb_runner_stub(runner_stub: RunnerStub, duckdb_conn: DuckDBPyConnection) -> RunnerStub:
    runner_stub._session = duckdb_conn
    return runner_stub


@pytest.fixture(autouse=True)
def duckdb_job_stub(job_stub: JobStub, duckdb_runner_stub: RunnerStub) -> JobStub:
    job_stub.runner = duckdb_runner_stub
    return job_stub


@pytest.fixture(autouse=True)
def duckdb_session(duckdb_job_stub: JobStub) -> Generator[Any, Any, None]:
    with Context.for_job(duckdb_job_stub) as context:
        yield context.runner.session


@pytest.fixture
def duckdb_runner() -> Generator[DuckdbRunner, Any, None]:
    """Returns a raw DuckdbRunner already set up with an in-memory connection."""
    runner: DuckdbRunner = DuckdbRunner(database=":memory:").__wrapped__
    runner.setup()
    yield runner
    runner.teardown()
