from collections.abc import Generator

import duckdb
import pytest
from duckdb import DuckDBPyConnection

from tiozin.assembly.runner_proxy import RunnerProxy


@pytest.fixture(scope="session", autouse=True)
def duckdb_session() -> Generator[DuckDBPyConnection, None, None]:
    conn = duckdb.connect(":memory:")
    token = RunnerProxy.active_session.set(conn)
    yield conn
    RunnerProxy.active_session.reset(token)
    conn.close()
