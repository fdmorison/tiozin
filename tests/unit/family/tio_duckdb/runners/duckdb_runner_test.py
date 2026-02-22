from pathlib import Path

import duckdb
import pytest

from tiozin.exceptions import NotInitializedError, TiozinInternalError
from tiozin.family.tio_duckdb.runners.duckdb_runner import DuckdbRunner


# =============================================================================
# Testing DuckdbRunner - Initialization
# =============================================================================
def test_runner_should_use_default_values_when_no_parameters_provided():
    # Act
    runner = DuckdbRunner()

    # Assert
    actual = (
        runner.database,
        runner.read_only,
        runner.attach,
        runner.extensions,
    )
    expected = (None, False, {}, [])
    assert actual == expected


@pytest.mark.parametrize(
    "kwargs,attr,expected",
    [
        ({"database": "path/to/main.duckdb"}, "database", "path/to/main.duckdb"),
        ({"read_only": True}, "read_only", True),
        (
            {"attach": {"analytics": "/data/analytics.duckdb"}},
            "attach",
            {"analytics": "/data/analytics.duckdb"},
        ),
        ({"extensions": ["httpfs", "spatial"]}, "extensions", ["httpfs", "spatial"]),
        ({"extensions": "httpfs"}, "extensions", ["httpfs"]),
        ({"threads": 4, "memory_limit": "2GB"}, "options", {"threads": 4, "memory_limit": "2GB"}),
    ],
)
def test_runner_should_store_parameter(kwargs: dict, attr: str, expected):
    # Act
    runner = DuckdbRunner(**kwargs)

    # Assert
    actual = getattr(runner, attr)
    assert actual == expected


# =============================================================================
# Testing DuckdbRunner - Session Property
# =============================================================================
def test_session_should_raise_not_initialized_error_before_setup():
    # Arrange
    runner = DuckdbRunner()

    # Act / Assert
    with pytest.raises(NotInitializedError):
        _ = runner.session


def test_session_should_return_connection_after_setup(
    duckdb_runner: DuckdbRunner,
):
    # Act
    actual = duckdb_runner.session

    # Assert
    assert isinstance(actual, duckdb.DuckDBPyConnection)


# =============================================================================
# Testing DuckdbRunner - Setup
# =============================================================================
def test_setup_should_use_in_memory_database_by_default():
    # Arrange
    runner: DuckdbRunner = DuckdbRunner().__wrapped__

    # Act
    runner.setup()

    # Assert
    actual = runner.session.sql("PRAGMA database_list").fetchone()[1]
    expected = "memory"
    assert actual == expected
    runner.teardown()


def test_setup_should_be_idempotent():
    # Arrange
    runner: DuckdbRunner = DuckdbRunner(database=":memory:").__wrapped__
    runner.setup()
    first_session = runner.session

    # Act
    runner.setup()

    # Assert
    actual = runner.session
    expected = first_session
    assert actual is expected
    runner.teardown()


def test_setup_should_attach_external_databases(tmp_path: Path):
    # Arrange
    ext_db_path = str(tmp_path / "external.duckdb")
    duckdb.connect(str(ext_db_path)).close()
    runner: DuckdbRunner = DuckdbRunner(
        attach={"ext": ext_db_path},
    ).__wrapped__

    # Act
    runner.setup()

    # Assert
    actual = [
        table[2] for table in runner.session.sql("SELECT * FROM duckdb_databases()").fetchall()
    ]
    expected = ext_db_path
    assert expected in actual
    runner.teardown()


def test_setup_should_load_extensions():
    # Arrange
    runner: DuckdbRunner = DuckdbRunner(
        database=":memory:",
        extensions=["httpfs"],
    ).__wrapped__

    # Act
    runner.setup()

    # Assert
    actual = runner.session.sql(
        "SELECT loaded FROM duckdb_extensions() WHERE extension_name = 'httpfs'"
    ).fetchone()[0]
    expected = True
    assert actual == expected
    runner.teardown()


# =============================================================================
# Testing DuckdbRunner - Teardown
# =============================================================================
def test_teardown_should_close_connection():
    # Arrange
    runner = DuckdbRunner(database=":memory:").__wrapped__
    runner.setup()

    # Act
    runner.teardown()

    # Assert
    with pytest.raises(NotInitializedError):
        _ = runner.session


def test_teardown_should_be_idempotent():
    # Arrange
    runner = DuckdbRunner(database=":memory:").__wrapped__
    runner.setup()

    # Act
    runner.teardown()
    runner.teardown()

    # Assert (no error raised)
    assert True


# =============================================================================
# Testing DuckdbRunner - Run
# =============================================================================
def test_run_should_execute_relation(duckdb_runner: DuckdbRunner):
    # Arrange
    conn = duckdb_runner.session
    relation = conn.sql("SELECT 1 AS id, 'Alice' AS name")

    # Act
    result = duckdb_runner.run(relation)

    # Assert
    actual = result[relation.alias]
    expected = [{"id": 1, "name": "Alice"}]
    assert actual == expected


def test_run_should_execute_sql_string(duckdb_runner: DuckdbRunner):
    # Arrange
    query = "SELECT 42 AS answer"

    # Act
    result = duckdb_runner.run(query)

    # Assert
    actual = result[duckdb_runner.context.name]
    expected = [{"answer": 42}]
    assert actual == expected


def test_run_should_execute_sql_string_with_params(duckdb_runner: DuckdbRunner):
    # Arrange
    query = "SELECT $val AS answer"
    params = {"val": 99}

    # Act
    result = duckdb_runner.run(query, params=params)

    # Assert
    actual = result[duckdb_runner.context.name]
    expected = [{"answer": 99}]
    assert actual == expected


@pytest.mark.parametrize("plan", ["", [None]])
def test_run_should_skip_empty_plan(duckdb_runner: DuckdbRunner, plan):
    # Act
    actual = duckdb_runner.run(plan)

    # Assert
    expected = {}
    assert actual == expected


def test_run_should_raise_error_for_unsupported_plan_type(
    duckdb_runner: DuckdbRunner,
):
    # Act / Assert
    with pytest.raises(TiozinInternalError, match="Unsupported DuckDB plan"):
        duckdb_runner.run(12345)


def test_run_should_execute_multiple_plans(duckdb_runner: DuckdbRunner):
    # Arrange
    conn = duckdb_runner.session
    plan1 = conn.sql("SELECT 1 AS id").set_alias("plan1")
    plan2 = conn.sql("SELECT 2 AS id").set_alias("plan2")

    # Act
    result = duckdb_runner.run([plan1, plan2])

    # Assert
    actual = result
    expected = {
        "plan1": [{"id": 1}],
        "plan2": [{"id": 2}],
    }
    assert actual == expected
