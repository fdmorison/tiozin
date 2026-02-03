import duckdb
import pytest
from duckdb import CatalogException, DuckDBPyConnection, DuckDBPyRelation

from tiozin.exceptions import InvalidInputError, RequiredArgumentError
from tiozin.family.tio_duckdb.assembly.read_builder import ReadBuilder

BASE_PATH = "./tests/mocks/data"


@pytest.fixture
def conn() -> DuckDBPyConnection:
    return duckdb.connect(":memory:")


# =============================================================================
# Testing ReadBuilder - Native Formats
# =============================================================================
def test_builder_should_read_parquet_files(conn):
    """Reads Parquet files into a DuckDB relation."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("parquet")
        .path(
            f"{BASE_PATH}/parquet/sample.parquet",
        )
        .load()
    )

    # Assert
    actual = sorted(relation.fetchall())
    expected = [
        ("hello spark",),
        ("hello world",),
    ]
    assert actual == expected


def test_builder_should_read_csv_files(conn):
    """Reads CSV files into a DuckDB relation."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("csv")
        .path(
            f"{BASE_PATH}/csv/sample.csv",
        )
        .load()
    )

    # Assert
    actual = sorted(relation.fetchall())
    expected = [("spark", "hello spark"), ("world", "hello world")]
    assert actual == expected


def test_builder_should_read_json_files(conn):
    """Reads JSON files into a DuckDB relation."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("json")
        .path(
            f"{BASE_PATH}/json/sample.json",
        )
        .load()
    )

    # Assert
    actual = sorted(relation.fetchall())
    expected = [
        ("hello spark",),
        ("hello world",),
    ]
    assert actual == expected


def test_builder_should_read_ndjson_files(conn):
    """Reads newline-delimited JSON files into a DuckDB relation."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("ndjson")
        .path(
            f"{BASE_PATH}/ndjson/sample.ndjson",
        )
        .load()
    )

    # Assert
    actual = sorted(relation.fetchall())
    expected = [
        ("hello spark",),
        ("hello world",),
    ]
    assert actual == expected


def test_builder_should_read_text_files(conn):
    """Reads plain text files with content renamed to value column."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("text")
        .path(
            f"{BASE_PATH}/text/sample.txt",
        )
        .load()
    )

    # Assert
    actual = relation.columns
    expected = ["value"]
    assert actual == expected

    actual = relation.fetchall()
    expected = [
        ("hello world\nhello spark\n",),
    ]
    assert actual == expected


def test_builder_should_read_blob_files(conn):
    """Reads binary files into a DuckDB relation."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("blob")
        .path(
            f"{BASE_PATH}/blob/sample.bin",
        )
        .load()
    )

    # Assert
    actual = relation.fetchall()
    expected = [
        (b"hello world\n",),
    ]
    assert actual == expected


# =============================================================================
# Testing ReadBuilder - Format Aliases
# =============================================================================
def test_builder_should_resolve_tsv_alias(conn):
    """Resolves tsv alias to read_csv with tab delimiter."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("tsv")
        .path(
            f"{BASE_PATH}/tsv/sample.tsv",
        )
        .load()
    )

    # Assert
    actual = sorted(relation.fetchall())
    expected = [
        ("spark", "hello spark"),
        ("world", "hello world"),
    ]
    assert actual == expected


def test_builder_should_resolve_jsonl_alias(conn):
    """Resolves jsonl alias to read_ndjson."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("jsonl")
        .path(
            f"{BASE_PATH}/ndjson/sample.ndjson",
        )
        .load()
    )

    # Assert
    actual = sorted(relation.fetchall())
    expected = [
        ("hello spark",),
        ("hello world",),
    ]
    assert actual == expected


def test_builder_should_resolve_txt_alias(conn):
    """Resolves txt alias to read_text."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("txt")
        .path(
            f"{BASE_PATH}/text/sample.txt",
        )
        .load()
    )

    # Assert
    actual = relation.fetchall()
    expected = [
        ("hello world\nhello spark\n",),
    ]
    assert actual == expected


# =============================================================================
# Testing ReadBuilder - Custom Options
# =============================================================================
def test_builder_should_pass_custom_options_to_reader(conn):
    """Custom options are forwarded to the DuckDB reader function."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("csv")
        .path(f"{BASE_PATH}/csv/sample.csv")
        .options(header=True, delim=",")
        .load()
    )

    # Assert
    actual = sorted(relation.fetchall())
    expected = [
        ("spark", "hello spark"),
        ("world", "hello world"),
    ]
    assert actual == expected


def test_builder_should_allow_overriding_alias_defaults(conn):
    """User options override alias defaults (e.g. overriding tsv delimiter)."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = (
        builder.format("tsv")
        .path(
            f"{BASE_PATH}/csv/sample.csv",
        )
        .options(delim=",")
        .load()
    )

    # Assert
    actual = sorted(relation.fetchall())
    expected = [
        ("spark", "hello spark"),
        ("world", "hello world"),
    ]
    assert actual == expected


# =============================================================================
# Testing ReadBuilder - Explode Filepath
# =============================================================================
@pytest.mark.parametrize(
    "format,path,filename,filestem,filetype",
    [
        ("csv", f"{BASE_PATH}/csv/sample.csv", "sample.csv", "sample", "csv"),
        ("json", f"{BASE_PATH}/json/sample.json", "sample.json", "sample", "json"),
        ("parquet", f"{BASE_PATH}/parquet/sample.parquet", "sample.parquet", "sample", "parquet"),
        ("ndjson", f"{BASE_PATH}/ndjson/sample.ndjson", "sample.ndjson", "sample", "ndjson"),
        ("tsv", f"{BASE_PATH}/tsv/sample.tsv", "sample.tsv", "sample", "tsv"),
        ("text", f"{BASE_PATH}/text/sample.txt", "sample.txt", "sample", "txt"),
        ("text", f"{BASE_PATH}/text/sample", "sample", "sample", ""),
        ("txt", f"{BASE_PATH}/text/sample.txt", "sample.txt", "sample", "txt"),
        ("blob", f"{BASE_PATH}/blob/sample.bin", "sample.bin", "sample", "bin"),
    ],
)
def test_builder_should_explode_filepath_when_enabled(
    conn,
    format: str,
    path: str,
    filename: str,
    filestem: str,
    filetype: str,
):
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = builder.format(format).path(path).with_explode_filepath().load()

    # Assert
    rows = relation.fetchall()
    actual = {
        col: rows[0][i]
        for i, col in enumerate(relation.columns)
        if col in ("filename", "filestem", "filetype")
    }
    expected = {
        "filename": filename,
        "filestem": filestem,
        "filetype": filetype,
    }
    assert actual == expected


@pytest.mark.parametrize(
    "format,path",
    [
        ("text", f"{BASE_PATH}/text/sample.txt"),
        ("blob", f"{BASE_PATH}/blob/sample.bin"),
    ],
)
def test_builder_should_include_filesize_for_text_and_blob(conn, format: str, path: str):
    """Text and blob formats include a filesize column derived from octet_length(content)."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = builder.format(format).path(path).with_explode_filepath().load()

    # Assert
    rows = relation.fetchall()
    actual = {col: rows[0][i] for i, col in enumerate(relation.columns) if col == "filesize"}
    assert "filesize" in actual
    assert actual["filesize"] > 0


def test_builder_should_not_explode_filepath_by_default(conn):
    """Filepath columns are absent by default."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = builder.format("csv").path(f"{BASE_PATH}/csv/sample.csv").load()

    # Assert
    actual = relation.columns
    expected = ["name", "greeting"]
    assert actual == expected


# =============================================================================
# Testing ReadBuilder - Load Modes
# =============================================================================
def test_builder_should_return_relation_by_default(conn):
    """Default mode returns a DuckDBPyRelation without registering anything."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    relation = builder.format("csv").path(f"{BASE_PATH}/csv/sample.csv").load()

    # Assert
    actual = (
        type(relation),
        sorted(relation.fetchall()),
    )
    expected = (
        DuckDBPyRelation,
        [("spark", "hello spark"), ("world", "hello world")],
    )
    assert actual == expected


def test_builder_should_register_temp_view(conn):
    """Mode temp_view registers a named temporary view via conn.register."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    builder.format("csv").path(f"{BASE_PATH}/csv/sample.csv").mode(
        "temp_view", "my_temp_view"
    ).load()

    # Assert
    actual = conn.sql(
        "SELECT temporary FROM duckdb_views() WHERE view_name = 'my_temp_view'"
    ).fetchone()
    expected = (True,)
    assert actual == expected


def test_builder_should_create_view(conn):
    """Mode view creates a persistent named view."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    builder.format("csv").path(
        f"{BASE_PATH}/csv/sample.csv",
    ).mode("view", "my_view").load()

    # Assert
    actual = conn.sql("SELECT temporary FROM duckdb_views() WHERE view_name = 'my_view'").fetchone()
    expected = (False,)
    assert actual == expected


def test_builder_should_create_table(conn):
    """Mode table creates a persistent table."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    builder.format("csv").path(
        f"{BASE_PATH}/csv/sample.csv",
    ).mode("table", "my_table").load()

    # Assert
    actual = conn.sql(
        "SELECT temporary FROM duckdb_tables() WHERE table_name = 'my_table'"
    ).fetchone()
    expected = (False,)
    assert actual == expected


def test_builder_should_create_temp_table(conn):
    """Mode temp_table creates a temporary table."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act
    builder.format("csv").path(
        f"{BASE_PATH}/csv/sample.csv",
    ).mode("temp_table", "my_temp_table").load()

    # Assert
    actual = conn.sql(
        "SELECT temporary FROM duckdb_tables() WHERE table_name = 'my_temp_table'"
    ).fetchone()
    expected = (True,)
    assert actual == expected


def test_builder_should_overwrite_existing_table(conn):
    """Mode overwrite_table creates or replaces a persistent table."""
    # Arrange
    builder = ReadBuilder(conn)
    builder.format("csv").path(
        f"{BASE_PATH}/csv/sample.csv",
    ).mode("table", "staging_table").load()

    # Act
    builder = ReadBuilder(conn)
    builder.format("csv").path(
        f"{BASE_PATH}/csv/sample.csv",
    ).mode("overwrite_table", "staging_table").load()

    # Assert
    actual = conn.sql(
        "SELECT temporary FROM duckdb_tables() WHERE table_name = 'staging_table'"
    ).fetchone()
    expected = (False,)
    assert actual == expected


# =============================================================================
# Testing ReadBuilder - Validation
# =============================================================================
def test_builder_should_raise_error_when_format_is_unsupported(conn):
    """Raises a DuckDB CatalogException for unsupported file formats."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act / Assert
    with pytest.raises(CatalogException):
        builder.format("my_format").path(f"{BASE_PATH}/text/sample.txt").load()


def test_builder_should_raise_error_when_format_is_missing(conn):
    """Raises RequiredArgumentError when format is None or empty."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act / Assert
    with pytest.raises(RequiredArgumentError):
        builder.format(None).path(f"{BASE_PATH}/csv/sample.csv").load()


def test_builder_should_raise_error_when_path_is_missing(conn):
    """Raises RequiredArgumentError when path is not set."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act / Assert
    with pytest.raises(RequiredArgumentError):
        builder.format("csv").load()


def test_builder_should_raise_error_when_mode_is_invalid(conn):
    """Raises InvalidInputError when mode is not a recognized load mode."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act / Assert
    with pytest.raises(InvalidInputError):
        builder.format("csv").path(f"{BASE_PATH}/csv/sample.csv").mode("invalid_mode", "x").load()


def test_builder_should_raise_error_when_mode_name_is_missing(conn):
    """Raises RequiredArgumentError when mode name is None or empty."""
    # Arrange
    builder = ReadBuilder(conn)

    # Act / Assert
    with pytest.raises(RequiredArgumentError):
        builder.format("csv").path(f"{BASE_PATH}/csv/sample.csv").mode("table", None).load()
