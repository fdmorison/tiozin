from tiozin.family.tio_duckdb import DuckdbPostgresOutput

# ============================================================================
# Testing DuckdbPostgresOutput.static_datasets — postgres namespace
# ============================================================================


def test_postgres_output_should_return_dataset_with_postgres_namespace():
    # Arrange
    step = DuckdbPostgresOutput(
        name="test",
        table="orders",
        host="pg.host",
        port=5432,
        database="mydb",
        schema="public",
    )

    # Act
    result = step.static_datasets()

    # Assert
    actual = (
        result.outputs[0].tiozin_namespace,
        result.outputs[0].tiozin_name,
    )
    expected = (
        "postgres://pg.host:5432",
        "mydb.public.orders",
    )
    assert actual == expected
