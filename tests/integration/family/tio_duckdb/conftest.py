from collections.abc import Generator
from typing import Any

import duckdb
import pytest
from duckdb import DuckDBPyConnection
from testcontainers.core.network import DockerClient, Network
from testcontainers.core.wait_strategies import LogMessageWaitStrategy
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.postgres import PostgresContainer

from tests.integration.family.tio_duckdb import env
from tests.stubs import JobStub, RunnerStub
from tiozin import Context
from tiozin.utils import randstr

TEST_ID = f"tiozin-test-{randstr()}"


# Mock Tiozins
@pytest.fixture(scope="function", autouse=True)
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


# Mock Data
@pytest.fixture()
def customers(duckdb_session: DuckDBPyConnection):
    dataset = "customers"
    data = duckdb_session.read_csv(f"tests/mocks/datasets/{dataset}.csv")
    data = data.set_alias(dataset)
    duckdb_session.register(dataset, data)
    yield data
    duckdb_session.unregister(dataset)


@pytest.fixture()
def customers_evolved(duckdb_session: DuckDBPyConnection):
    dataset = "customers_evolved"
    data = duckdb_session.read_csv(f"tests/mocks/datasets/{dataset}.csv")
    data = data.set_alias(dataset)
    duckdb_session.register(dataset, data)
    yield data
    duckdb_session.unregister(dataset)


@pytest.fixture()
def customers_updated(duckdb_session: DuckDBPyConnection):
    dataset = "customers_updated"
    data = duckdb_session.read_csv(f"tests/mocks/datasets/{dataset}.csv")
    data = data.set_alias(dataset)
    duckdb_session.register(dataset, data)
    yield data
    duckdb_session.unregister(dataset)


# Mock External Systems
@pytest.fixture(scope="session", autouse=True)
def tiozinnet():
    client = DockerClient()
    network = client.client_networks_create(
        f"{TEST_ID}-net",
        {"driver": "bridge"},
    )
    return network


# Postgres
@pytest.fixture(scope="session", autouse=True)
def postgres15(request: pytest.FixtureRequest, tiozinnet: Network) -> None:
    postgres = PostgresContainer(
        dbname=env.PGDATABASE,
        username=env.PGUSER,
        password=env.PGPASSWORD,
        image="postgres:15-alpine",
    )
    postgres.with_name(f"{TEST_ID}-postgres")
    postgres.with_bind_ports(5432, env.PGPORT)
    postgres.with_network(tiozinnet)
    postgres.with_network_aliases(postgres._name)

    postgres.start()
    wait_for_logs(postgres, LogMessageWaitStrategy("server started"))
    request.addfinalizer(lambda: postgres.stop())


@pytest.fixture(autouse=True)
def postgres_reset() -> Generator[None, None, None]:
    yield
    import psycopg2

    conn = psycopg2.connect(
        host=env.PGHOST,
        port=env.PGPORT,
        dbname=env.PGDATABASE,
        user=env.PGUSER,
        password=env.PGPASSWORD,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    conn.close()
