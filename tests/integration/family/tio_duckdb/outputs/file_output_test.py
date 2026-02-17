from pathlib import Path

from duckdb import DuckDBPyConnection

from tiozin.family.tio_duckdb import DuckdbFileOutput


# =============================================================================
# Testing DuckdbFileOutput - Initialization
# =============================================================================
def test_output_should_default_to_parquet_format():
    # Act
    output = DuckdbFileOutput(name="test", path="/tmp/data")

    # Assert
    actual = output.format
    expected = "parquet"
    assert actual == expected


def test_output_should_default_to_append_mode():
    # Act
    output = DuckdbFileOutput(name="test", path="/tmp/data")

    # Assert
    actual = output.mode
    expected = "APPEND"
    assert actual == expected


def test_output_should_default_to_snappy_compression():
    # Act
    output = DuckdbFileOutput(name="test", path="/tmp/data")

    # Assert
    actual = output.compression
    expected = "snappy"
    assert actual == expected


def test_output_should_ensure_path_ends_with_slash():
    # Act
    output = DuckdbFileOutput(name="test", path="/tmp/data")

    # Assert
    actual = output.path
    expected = "/tmp/data/"
    assert actual == expected


# =============================================================================
# Testing DuckdbFileOutput - Write Behavior
# =============================================================================
def test_output_should_return_copy_sql_for_parquet(
    duckdb_session: DuckDBPyConnection, tmp_path: Path
):
    """write() returns a COPY SQL string for parquet format."""
    # Arrange
    data = duckdb_session.sql(
        "SELECT * FROM (VALUES ('hello', 1), ('world', 2)) AS t(word, count)"
    ).set_alias("data")
    duckdb_session.register("data", data)
    output_path = str(tmp_path / "parquet")

    # Act
    actual = DuckdbFileOutput(
        name="test",
        path=output_path,
        format="parquet",
        mode="overwrite",
    ).write(data)

    # Assert
    expected = (
        f"COPY data TO '{output_path}/' ("
        "FORMAT parquet,"
        "FILENAME_PATTERN 'part-{i}-{uuidv7}.snappy',"
        "COMPRESSION snappy,"
        "OVERWRITE 1,"
        "PER_THREAD_OUTPUT true)"
    )
    assert actual == expected


def test_output_should_return_copy_sql_for_json(duckdb_session: DuckDBPyConnection, tmp_path: Path):
    """write() returns a COPY SQL string for json format."""
    # Arrange
    data = duckdb_session.sql(
        "SELECT * FROM (VALUES ('hello',), ('spark',)) AS t(value)"
    ).set_alias("json_data")
    duckdb_session.register("json_data", data)
    output_path = str(tmp_path / "json")

    # Act
    actual = DuckdbFileOutput(
        name="test",
        path=output_path,
        format="json",
        mode="overwrite",
        compression="uncompressed",
    ).write(data)

    # Assert
    expected = (
        f"COPY json_data TO '{output_path}/' ("
        "FORMAT json,"
        "FILENAME_PATTERN 'part-{i}-{uuidv7}.uncompressed',"
        "COMPRESSION uncompressed,"
        "OVERWRITE 1,"
        "PER_THREAD_OUTPUT true)"
    )
    assert actual == expected


def test_output_should_return_copy_sql_for_partitioned_data(
    duckdb_session: DuckDBPyConnection, tmp_path: Path
):
    """write() returns a COPY SQL string with PARTITION_BY when partition_by is provided."""
    # Arrange
    data = duckdb_session.sql("""
        SELECT * FROM (VALUES
            ('2024-01-01', 'hello'),
            ('2024-01-02', 'world')
        ) AS t(date, value)
    """).set_alias("partitioned")
    duckdb_session.register("partitioned", data)
    output_path = str(tmp_path / "partitioned")

    # Act
    actual = DuckdbFileOutput(
        name="test",
        path=output_path,
        format="parquet",
        mode="overwrite",
        partition_by=["date"],
    ).write(data)

    # Assert
    expected = (
        f"COPY partitioned TO '{output_path}/' ("
        "FORMAT parquet,"
        "FILENAME_PATTERN 'part-{i}-{uuidv7}.snappy',"
        "COMPRESSION snappy,"
        "OVERWRITE 1,"
        "PARTITION_BY (date))"
    )
    assert actual == expected
