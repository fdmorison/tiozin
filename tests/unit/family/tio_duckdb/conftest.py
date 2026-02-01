from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import duckdb
import pytest
from duckdb import DuckDBPyConnection

from tiozin import Context
from tiozin.assembly.runner_proxy import RunnerProxy
from tiozin.family.tio_duckdb import DuckdbRunner


@pytest.fixture(scope="session", autouse=True)
def duckdb_session() -> Generator[DuckDBPyConnection, None, None]:
    conn = duckdb.connect(":memory:")
    token = RunnerProxy.active_session.set(conn)
    yield conn
    RunnerProxy.active_session.reset(token)
    conn.close()


@pytest.fixture
def context() -> Context:
    ctx = MagicMock(spec=Context)
    ctx.job = MagicMock()
    ctx.job.name = "test_job"
    ctx.name = "test_step"
    ctx.execution_delay = 0.0
    return ctx


@pytest.fixture
def raw_runner() -> DuckdbRunner:
    """Returns the unwrapped DuckdbRunner (bypasses RunnerProxy)."""
    proxy = DuckdbRunner(database=":memory:")
    return proxy.__wrapped__


@pytest.fixture
def runner_with_session(
    raw_runner: DuckdbRunner, context: Context
) -> Generator[DuckdbRunner, Any, None]:
    """Returns a raw DuckdbRunner already set up with an in-memory connection."""
    raw_runner.setup(context)
    yield raw_runner
    raw_runner.teardown(context)
