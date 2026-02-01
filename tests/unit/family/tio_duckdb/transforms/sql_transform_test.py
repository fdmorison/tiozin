import pytest
from duckdb import (
    CatalogException,
    DuckDBPyConnection,
    ParserException,
)

from tiozin.family.tio_duckdb import DuckdbSqlTransform

# =============================================================================
# Testing DuckdbSqlTransform - Core Behavior
# =============================================================================


def test_transform_should_execute_sql_using_existing_view(duckdb_session: DuckDBPyConnection):
    """Executes SQL against existing views without relying on the @self token."""
    # Arrange
    duckdb_session.sql("""
        CREATE OR REPLACE VIEW customers AS
        SELECT * FROM (VALUES (1, 'Alice'), (2, 'Bob')) AS t(id, name)
    """)
    input_rel = duckdb_session.sql("SELECT 1 AS dummy").set_alias("input")
    context = None

    # Act
    relation = DuckdbSqlTransform(
        name="sql_existing_view",
        query="SELECT * FROM customers",
    ).transform(context, input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [(1, "Alice"), (2, "Bob")]
    assert actual == expected


def test_transform_should_execute_sql_using_multiple_existing_views(
    duckdb_session: DuckDBPyConnection,
):
    """Executes a SQL query that joins multiple existing views."""
    # Arrange
    duckdb_session.sql("""
        CREATE OR REPLACE VIEW customers AS
        SELECT * FROM (VALUES (1, 'Alice'), (2, 'Bob')) AS t(id, name)
    """)
    duckdb_session.sql("""
        CREATE OR REPLACE VIEW orders AS
        SELECT * FROM (VALUES (1, 100.0), (2, 50.0)) AS t(customer_id, total)
    """)
    input_rel = duckdb_session.sql("SELECT * FROM customers").set_alias("customers")
    context = None

    # Act
    relation = DuckdbSqlTransform(
        name="sql_multi_view",
        query="""
            SELECT c.id, c.name, o.total
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
        """,
    ).transform(context, input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [(1, "Alice", 100.0), (2, "Bob", 50.0)]
    assert actual == expected


def test_transform_should_bind_single_dataframe_as_self(duckdb_session: DuckDBPyConnection):
    """Resolves the @self token to the input relation's alias."""
    # Arrange
    input_rel = duckdb_session.sql(
        "SELECT * FROM (VALUES (1, 100.0), (2, 50.0)) AS t(id, total)"
    ).set_alias("my_input")
    duckdb_session.register("my_input", input_rel)
    context = None

    # Act
    relation = DuckdbSqlTransform(
        name="sql_self",
        query="SELECT * FROM @self WHERE total > 80",
    ).transform(context, input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [(1, 100.0)]
    assert actual == expected


def test_transform_should_bind_multiple_dataframes_as_self_sequence(
    duckdb_session: DuckDBPyConnection,
):
    """Resolves @self and @self1 to their respective input aliases."""
    # Arrange
    customers = duckdb_session.sql(
        "SELECT * FROM (VALUES (1, 'Alice'), (2, 'Bob')) AS t(id, name)"
    ).set_alias("customers")
    regions = duckdb_session.sql(
        "SELECT * FROM (VALUES (1, 'EU'), (2, 'US')) AS t(id, region)"
    ).set_alias("regions")

    duckdb_session.register("customers", customers)
    duckdb_session.register("regions", regions)

    # Act
    relation = DuckdbSqlTransform(
        name="sql_multi_input",
        query="""
            SELECT c.id, c.name, r.region
            FROM @self0 c
            JOIN @self1 r ON c.id = r.id
        """,
    ).transform(None, customers, regions)

    # Assert
    actual = relation.fetchall()
    expected = [(1, "Alice", "EU"), (2, "Bob", "US")]
    assert actual == expected


def test_transform_should_execute_sql_on_empty_relation(duckdb_session: DuckDBPyConnection):
    """Propagates an empty input through SQL execution."""
    # Arrange
    input_rel = duckdb_session.sql(
        "SELECT * FROM (VALUES (1, 'x')) AS t(id, name) WHERE false"
    ).set_alias("empty")
    duckdb_session.register("empty", input_rel)
    context = None

    # Act
    relation = DuckdbSqlTransform(
        name="sql_empty",
        query="SELECT * FROM @self",
    ).transform(context, input_rel)

    # Assert
    actual = relation.fetchall()
    expected = []
    assert actual == expected


def test_transform_should_accept_args_parameter(duckdb_session: DuckDBPyConnection):
    """Binds named parameters to the SQL query."""
    # Arrange
    input_rel = duckdb_session.sql(
        "SELECT * FROM (VALUES (1, 'Alice', 100.0), (2, 'Bob', 50.0)) AS t(id, name, total)"
    ).set_alias("data")
    duckdb_session.register("data", input_rel)
    context = None

    # Act
    relation = DuckdbSqlTransform(
        name="sql_args",
        query="SELECT * FROM @self WHERE total > $min_total",
        args={"min_total": 80.0},
    ).transform(context, input_rel)

    # Assert
    actual = relation.fetchall()
    expected = [(1, "Alice", 100.0)]
    assert actual == expected


# =============================================================================
# Testing DuckdbSqlTransform - Failure Scenarios
# =============================================================================


def test_transform_should_fail_when_referenced_view_does_not_exist(
    duckdb_session: DuckDBPyConnection,
):
    # Arrange
    input_rel = duckdb_session.sql("SELECT 1 AS value").set_alias("input")
    duckdb_session.register("input", input_rel)
    context = None

    # Act / Assert
    with pytest.raises(CatalogException):
        DuckdbSqlTransform(
            name="sql_missing",
            query="SELECT * FROM does_not_exist",
        ).transform(context, input_rel)


def test_transform_should_fail_when_sql_is_invalid(duckdb_session: DuckDBPyConnection):
    # Arrange
    input_rel = duckdb_session.sql("SELECT 1 AS value").set_alias("input")
    duckdb_session.register("input", input_rel)
    context = None

    # Act / Assert
    with pytest.raises((ParserException, CatalogException)):
        DuckdbSqlTransform(
            name="sql_invalid",
            query="SELECXXX * FROM @self",
        ).transform(context, input_rel)
